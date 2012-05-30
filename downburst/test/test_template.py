from .. import template


def test_domain_name():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
        )
    name = tree.xpath('/domain/name/text()')
    name = ''.join(name)
    assert name == 'fakename'


def test_domain_disk():
    tree = template.domain(
        name='fakename',
        disk_key='/fake/path',
        iso_key='/fake/iso',
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
        )
    got = tree.xpath(
        '/domain/devices/disk[@device="cdrom"]/source/@file',
        )
    assert got == ['/fake/iso']
