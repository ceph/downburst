from .. import template


def test_domain_name():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        emulator='/fake/emulator/path',
        )
    name = tree.xpath('/domain/name/text()')
    name = ''.join(name)
    assert name == 'fakename'


def test_domain_arch():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        emulator='/fake/emulator/path',
        )
    arch = tree.xpath('/domain/os/type/@arch')
    assert arch == ['x86_64']


def test_domain_disk():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        emulator='/fake/emulator/path',
        )
    got = tree.xpath(
        '/domain/devices/disk[@device="disk"]/source/@file',
        )
    assert got == ['/fake/path']


def test_domain_iso():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        emulator='/fake/emulator/path',
        )
    got = tree.xpath(
        '/domain/devices/disk[@device="cdrom"]/source/@file',
        )
    assert got == ['/fake/iso']


def test_domain_network_default():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        emulator='/fake/emulator/path',
        )
    got = tree.xpath(
        '/domain/devices/interface[@type="network"]/source/@network',
        )
    assert got == ['default']


def test_domain_network_custom():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        networks=[
            dict(source='one'),
            dict(source='two'),
            ],
        emulator='/fake/emulator/path',
        )
    got = tree.xpath(
        '/domain/devices/interface[@type="network"]/source/@network',
        )
    assert got == ['one', 'two']


def test_domain_network_mac():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        networks=[
            dict(mac='12:34:56:78:90:ab'),
            ],
        emulator='/fake/emulator/path',
        )
    got = tree.xpath(
        '/domain/devices/interface[@type="network"]/mac/@address',
        )
    assert got == ['12:34:56:78:90:ab']
