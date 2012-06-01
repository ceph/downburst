import libvirt
import logging

from lxml import etree

from . import image
from . import iso
from . import exc
from . import template


log = logging.getLogger(__name__)


def create(args):
    log.debug('Connecting to libvirt...')
    conn = libvirt.open('qemu:///system')
    if conn is None:
        raise exc.LibvirtConnectionError()

    # check if the vm exists already, complain if so. this would
    # normally use conn.lookupByName, but that logs on all errors;
    # avoid the noise.
    if args.name in conn.listDefinedDomains():
        raise exc.VMExistsError(args.name)

    log.debug('Opening libvirt pool...')
    pool = conn.storagePoolLookupByName('default')

    vol = image.ensure_cloud_image()
    clonexml = template.volume_clone(
        name='{name}.img'.format(name=args.name),
        parent_vol=vol,
        )
    clone = pool.createXML(etree.tostring(clonexml), flags=0)

    iso_vol = iso.create_meta_iso(
        pool=pool,
        name=args.name,
        extra_meta=args.meta_data,
        extra_user=args.user_data,
        )

    domainxml = template.domain(
        name=args.name,
        disk_key=clone.key(),
        iso_key=iso_vol.key(),
        )
    dom = conn.defineXML(etree.tostring(domainxml))
    dom.create()


def make(parser):
    """
    Create an Ubuntu Cloud Image vm
    """
    parser.add_argument(
        '--user-data',
        metavar='FILE',
        help='extra user-data, a cloud-config-archive or arbitrary file',
        )
    parser.add_argument(
        '--meta-data',
        metavar='FILE',
        help='extra meta-data, must contain a yaml mapping',
        )
    parser.add_argument(
        'name',
        metavar='NAME',
        help='unique name to give to the vm',
        # TODO check valid syntax for hostname
        )
    parser.set_defaults(func=create)
