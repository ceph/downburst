import libvirt
import logging

from lxml import etree

from . import dehumanize
from . import image
from . import iso
from . import exc
from . import meta
from . import template
from . import wait

log = logging.getLogger(__name__)


def create(args):
    log.debug('Connecting to libvirt...')
    conn = libvirt.open(args.connect)
    if conn is None:
        raise exc.LibvirtConnectionError()

    meta_data = meta.gen_meta(
        name=args.name,
        extra_meta=args.meta_data,
        nokey=args.nokey,
        )

    user_data = meta.gen_user(
        name=args.name,
        extra_user=args.user_data,
        )

    if args.distro:
        distro = args.distro
    else:
        distro = meta_data.get('downburst', {}).get('distro')

    if distro is None:
        distro = "ubuntu"

    if args.distroversion:
        distroversion = args.distroversion
    else:
        distroversion = meta_data.get('downburst', {}).get('distroversion')

    if distroversion is None:
        defaultversion = dict(
            ubuntu="12.04",
            fedora="17",
            centos="6.3",
            opensuse="12.2",
            sles="11-sp2",
            )
        distroversion = defaultversion[distro]

    if args.arch:
        arch = args.arch
    else:
        arch = meta_data.get('downburst', {}).get('arch')

    if arch == "x86_64":
        arch = "amd64"

    if arch is None:
        arch = "amd64"

    # check if the vm exists already, complain if so. this would
    # normally use conn.lookupByName, but that logs on all errors;
    # avoid the noise.
    if args.name in conn.listDefinedDomains():
        raise exc.VMExistsError(args.name)

    log.debug('Opening libvirt pool...')
    pool = conn.storagePoolLookupByName('default')
    vol = image.ensure_cloud_image(conn=conn, distro=distro, distroversion=distroversion, arch=arch)

    if args.wait:
        user_data.append("""\
#!/bin/sh
# eject the cdrom (containing the cloud-init metadata)
# as a signal that we've reached full functionality;
# this is used by ``downburst create --wait``
exec eject /dev/cdrom
""")

    capacity = meta_data.get('downburst', {}).get('disk-size', '10G')
    capacity = dehumanize.parse(capacity)
    additional_disks = meta_data.get('downburst', {}).get('additional-disks')
    additional_disks_size = meta_data.get('downburst', {}).get('additional-disks-size', '10G')
    additional_disks_size = dehumanize.parse(additional_disks_size)

    clonexml = template.volume_clone(
        name='{name}.img'.format(name=args.name),
        parent_vol=vol,
        capacity=capacity,
        )
    clone = pool.createXML(etree.tostring(clonexml), flags=0)

    iso_vol = iso.create_meta_iso(
        pool=pool,
        name=args.name,
        meta_data=meta_data,
        user_data=user_data,
        )

    # We want the range to be 2 - X depending on disk count.
    # Since there is already a boot volume we want the image
    # names to be appended with -2, -3, -4, etc... for the 
    # additional disks.
    additional_disks_key = []
    if additional_disks is not None:
        for disknum in range(1, additional_disks + 1):
            disknum += 1
            diskname = args.name + '-' + str(disknum) + '.img'
            diskxml = template.volume(
                name=diskname,
                capacity=additional_disks_size,
                format_='raw',
                sparse=False,
                )
            additional_disks_key.append(pool.createXML(etree.tostring(diskxml), flags=0).key())
    if not additional_disks_key:
        additional_disks_key = None

    ram = meta_data.get('downburst', {}).get('ram')
    ram = dehumanize.parse(ram)
    cpus = meta_data.get('downburst', {}).get('cpus')
    networks = meta_data.get('downburst', {}).get('networks')
    domainxml = template.domain(
        name=args.name,
        disk_key=clone.key(),
        iso_key=iso_vol.key(),
        ram=ram,
        cpus=cpus,
        networks=networks,
        additional_disks_key=additional_disks_key
        )
    dom = conn.defineXML(etree.tostring(domainxml))
    dom.create()

    if args.wait:
        log.debug('Waiting for vm to be initialized...')
        wait.wait_for_cdrom_eject(dom)


def make(parser):
    """
    Create an Ubuntu Cloud Image vm
    """
    parser.add_argument(
        '--user-data',
        metavar='FILE',
        action='append',
        help='extra user-data, a cloud-config-archive or arbitrary file',
        )
    parser.add_argument(
        '--meta-data',
        metavar='FILE',
        action='append',
        help='extra meta-data, must contain a yaml mapping',
        )
    parser.add_argument(
        '--wait',
        action='store_true',
        help='wait for VM to initialize',
        )
    parser.add_argument(
        '--distro',
        metavar='DISTRO',
        help='Distribution of the vm',
        )
    parser.add_argument(
        '--distroversion',
        metavar='DISTROVERSION',
        help='Distribution version of the vm',
        )
    parser.add_argument(
        '--nokey',
        action='store_true',
        help='Do not add the default ssh key (from Inktank teuthology) to authorized_hosts. Should be used for non-Inktank machines',
        )
    parser.add_argument(
        '--arch',
        metavar='arch',
        help='Architecture of the vm (amd64/i386)',
        )
    parser.add_argument(
        'name',
        metavar='NAME',
        help='unique name to give to the vm',
        # TODO check valid syntax for hostname
        )
    parser.set_defaults(
        func=create,
        distro=[],
        distroversion=[],
        user_data=[],
        meta_data=[],
        )
