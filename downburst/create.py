import libvirt
import logging

from lxml import etree

from . import image
from . import exc
from . import template


log = logging.getLogger(__name__)


def create(args):
    """
    Create an Ubuntu Cloud Image vm.
    """
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

    domainxml = template.domain(
        name=args.name,
        disk_key=clone.key(),
        iso_key='/var/lib/libvirt/images/cloud-init.{name}.iso'.format(name=args.name), # TODO
        )
    dom = conn.defineXML(etree.tostring(domainxml))
    dom.create()


def make(parser):
    """
    Create a vm
    """
    parser.add_argument(
        'name',
        metavar='NAME',
        help='unique name to give to the vm',
        # TODO check valid syntax for hostname
        )
    parser.set_defaults(func=create)
