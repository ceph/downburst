import json
import libvirt_qemu
import time

from . import exc


def is_cdrom_tray_open(domain):
    """
    Returns True if even one CD-ROM tray is open.
    """
    res = libvirt_qemu.qemuMonitorCommand(
        domain,
        json.dumps(
            {'execute': 'query-block'},
            ),
        # TODO should force this to be qmp, but python-libvirt 0.9.8
        # doesn't seem to be able to do that
        libvirt_qemu.VIR_DOMAIN_QEMU_MONITOR_COMMAND_DEFAULT,
        )
    res = json.loads(res)
    if 'error' in res:
        raise exc.DownburstError(
            'Cannot query QEmu for block device state',
            res['error'].get('desc'),
            )

    cdroms = [dev for dev in res['return'] if 'tray_open' in dev]
    if not cdroms:
        raise exc.DownburstError(
            'VM must have at least one CD-ROM to check tray status',
            res['error'].get('desc'),
            )

    for dev in cdroms:
        if dev['tray_open']:
            return True

    return False


def wait_for_cdrom_eject(domain):
    cd_ejected = False
    while not cd_ejected:
        cd_ejected = is_cdrom_tray_open(domain)

        if not cd_ejected:
            time.sleep(1)
