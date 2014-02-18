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
from . import discover

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

    # If ubuntu distroversion contains non version (IE: quantal) convert to version:
    if distroversion:
        if distro == 'ubuntu' and ('.' not in distroversion):
            handler = discover.UbuntuHandler()
            distroversion = handler.get_version(distroversion)

    if distroversion is None:
        defaultversion = dict(
            ubuntu="12.04",
            fedora="17",
            centos="6.3",
            opensuse="12.2",
            sles="11-sp2",
            rhel="6.3",
            debian='6.0'
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

    # Check if pool with same name of guest exists, use it if it does
    pool = ''
    pools = conn.listStoragePools()
    for poolentry in pools:
        if poolentry == args.name:
            pool = conn.storagePoolLookupByName(poolentry)
            break
    if not pool:
        pool = conn.storagePoolLookupByName('default')

    vol, raw = image.ensure_cloud_image(pool=pool, distro=distro, distroversion=distroversion, arch=arch, forcenew=args.forcenew)

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
    ceph_cluster_name = meta_data.get('downburst', {}).get('ceph-cluster-name')
    ceph_cluster_monitors = meta_data.get('downburst', {}).get('ceph-cluster-monitors')
    ceph_cluster_pool = meta_data.get('downburst', {}).get('ceph-cluster-pool')
    ceph_cluster_user = meta_data.get('downburst', {}).get('ceph-cluster-user')
    ceph_cluster_secret = meta_data.get('downburst', {}).get('ceph-cluster-secret')
    rbd_disks = meta_data.get('downburst', {}).get('rbd-disks')
    rbd_disks_size = dehumanize.parse(meta_data.get('downburst', {}).get('rbd-disks-size'))
    rbd_details = dict()
    rbd_details['ceph_cluster_name'] = ceph_cluster_name
    rbd_details['ceph_cluster_monitors'] = ceph_cluster_monitors
    rbd_details['ceph_cluster_pool'] = ceph_cluster_pool
    rbd_details['ceph_cluster_user'] = ceph_cluster_user
    rbd_details['ceph_cluster_secret'] = ceph_cluster_secret


    clonexml = template.volume_clone(
        name='{name}.img'.format(name=args.name),
        parent_vol=vol,
        capacity=capacity,
        raw=raw,
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

    rbd_disks_key = []
    if rbd_disks:
        assert ceph_cluster_name != None, "Unable to setup RBD Storage Pool. Pool name Required but is: %s" % pool
        try:
            rbdpool = conn.storagePoolLookupByName(ceph_cluster_name)
        except libvirt.libvirtError:
            poolxml = template.rbd_pool(
                name=ceph_cluster_name,
                monitorlist=ceph_cluster_monitors,
                pool=ceph_cluster_pool,
                user=ceph_cluster_user,
                secret=ceph_cluster_secret,
                )
            conn.storagePoolCreateXML(etree.tostring(poolxml), 0)
            rbdpool = conn.storagePoolLookupByName(ceph_cluster_name)

        if not additional_disks:
            additional_disks = 0
        for rbdnum in range(1 + additional_disks, additional_disks + rbd_disks + 1):
            rbdnum += 1
            rbdname = '{name}-{rbdnum}'.format(name=args.name, rbdnum=rbdnum)
            rbdxml = template.rbd_volume(
                name=rbdname,
                capacity=rbd_disks_size,
                pool=ceph_cluster_pool,
                )
            rbd_disks_key.append(rbdpool.createXML(etree.tostring(rbdxml), flags=0).key())
    if not rbd_disks_key:
        rbd_disks_key = None

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
        additional_disks_key=additional_disks_key,
        rbd_disks_key=rbd_disks_key,
        rbd_details=rbd_details,
        hypervisor=args.hypervisor
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
        '--forcenew',
        action='store_true',
        help='Instead if the cloud-init image already exists, force the attempt to download newest available image',
        )
    parser.add_argument(
        '--arch',
        metavar='arch',
        help='Architecture of the vm (amd64/i386)',
        )
    parser.add_argument(
        '--hypervisor',
        metavar='HYPERVISOR',
        help='The hypervisor used (kvm)'),
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
        hypervisor='kvm',
        )
