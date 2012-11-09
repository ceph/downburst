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
            )
        distroversion = defaultversion[distro]

    # check if the vm exists already, complain if so. this would
    # normally use conn.lookupByName, but that logs on all errors;
    # avoid the noise.
    if args.name in conn.listDefinedDomains():
        raise exc.VMExistsError(args.name)

    log.debug('Opening libvirt pool...')
    pool = conn.storagePoolLookupByName('default')
    vol = image.ensure_cloud_image(conn=conn, distro=distro, distroversion=distroversion)

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
