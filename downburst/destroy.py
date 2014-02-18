import libvirt
import logging
import re

log = logging.getLogger(__name__)


def looks_like_downburst_volume(name, vol_name):
    # {name}.img: the primary disk for the vm
    if vol_name == '{0}.img'.format(name):
        return True

    # additional disks for the vm
    if re.match(name + '-(\d+).img', vol_name):
        return True

    # cloud-init.{name}.iso: cloud-init meta-data CD-ROM
    if (vol_name.startswith('cloud-init.{0}.'.format(name))
        and vol_name.endswith('.iso')):
        return True

    # {name}.*.img: secondary data disks added after creation
    if (vol_name.startswith('{0}.'.format(name))
        and vol_name.endswith('.img')):
        return True

    # RBD backed objects
    if vol_name == name:
        return True

    # additional RBD backed objects
    if re.match(name + '-(\d+)', vol_name):
        return True

    return False


def destroy(args):
    log.debug('Connecting to libvirt...')
    conn = libvirt.open(args.connect)
    if conn is None:
        raise exc.LibvirtConnectionError()

    try:
        dom = conn.lookupByName(args.name)
    except libvirt.libvirtError as e:
        if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
            # the vm does not exist, but the associated volumes might
            # still exist
            log.debug('No virtual machine found.')
            pass
        else:
            raise
    else:
        # losing unsynced data is fine here; we're going to remove the
        # disk images next
        log.debug('Terminating the virtual machine')

        try:
            dom.destroy()
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_OPERATION_INVALID:
                # it wasn't running
                pass
            else:
                raise

        dom.undefineFlags(
             libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE
             | libvirt.VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA,
             )

    # we're going to remove all disks that look remotely like they
    # could be downburst vm related

    # TODO to make this safe, move the images to be prefixed with
    # e.g. "downburst."

    log.debug('Getting livirt pool list...')
    for poolentry in conn.listStoragePools():
        log.debug('Checking Pool: {pool}'.format(pool=poolentry))
        pool = conn.storagePoolLookupByName(poolentry)

        for vol_name in pool.listVolumes():
            log.debug('Checking Volumel: {volume}'.format(volume=vol_name))
            if looks_like_downburst_volume(
                name=args.name,
                vol_name=vol_name,
                ):
                log.debug('Deleting volume: %r', vol_name)
                vol = pool.storageVolLookupByName(vol_name)
                vol.delete(flags=0)


def make(parser):
    """
    Destroy a vm and its data.
    """
    parser.add_argument(
        'name',
        metavar='NAME',
        help='name of the vm to destroy',
        # TODO check valid syntax for hostname
        )
    parser.set_defaults(
        func=destroy,
        )
