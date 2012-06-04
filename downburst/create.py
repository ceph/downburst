import libvirt
import logging

from lxml import etree

from . import image
from . import iso
from . import exc
from . import meta
from . import template


log = logging.getLogger(__name__)


def create(args):
    log.debug('Connecting to libvirt...')
    conn = libvirt.open(args.connect)
    if conn is None:
        raise exc.LibvirtConnectionError()

    # check if the vm exists already, complain if so. this would
    # normally use conn.lookupByName, but that logs on all errors;
    # avoid the noise.
    if args.name in conn.listDefinedDomains():
        raise exc.VMExistsError(args.name)

    log.debug('Opening libvirt pool...')
    pool = conn.storagePoolLookupByName('default')

    vol = image.ensure_cloud_image(conn=conn)
    clonexml = template.volume_clone(
        name='{name}.img'.format(name=args.name),
        parent_vol=vol,
        )
    clone = pool.createXML(etree.tostring(clonexml), flags=0)

    meta_data = meta.gen_meta(
        name=args.name,
        extra_meta=args.meta_data,
        )
    user_data = meta.gen_user(
        name=args.name,
        extra_user=args.user_data,
        )
    iso_vol = iso.create_meta_iso(
        pool=pool,
        name=args.name,
        meta_data=meta_data,
        user_data=user_data,
        )

    ram = meta_data.get('downburst', {}).get('ram')
    domainxml = template.domain(
        name=args.name,
        disk_key=clone.key(),
        iso_key=iso_vol.key(),
        ram=ram,
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
        'name',
        metavar='NAME',
        help='unique name to give to the vm',
        # TODO check valid syntax for hostname
        )
    parser.set_defaults(
        func=create,
        user_data=[],
        meta_data=[],
        )
