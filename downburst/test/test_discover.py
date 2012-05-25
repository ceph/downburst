from .. import discover


def test_extract():
    PATH = (
        'server/releases/precise/release-20120424'
        + '/ubuntu-12.04-server-cloudimg-amd64-disk1.img'
        )
    URL = 'https://cloud-images.ubuntu.com/' + PATH
    SHA512 = (
        '0737607be5c9b8ef9b7c45a77802b0098ce99d73'
        + '7e1a233e1e582f98ea10b6619dcb280bb7e5c6ce'
        + 'fcba275473e9be56a7058fea534db7534908d3d0'
        + '83c569bd'
        )
    catalog = dict(
        catalog=[
            dict(
                distro_code_name='oneiric',
                borkbork=True,
                ),
            dict(
                distro_code_name='precise',
                build_types=dict(
                    misleading='bork bork',
                    server=[
                        dict(
                            release_tag='daily',
                            borkbork=True,
                            ),
                        dict(
                            release_tag='release',
                            build_serial='20120424',
                            arches=dict(
                                misleading='bork bork',
                                amd64=dict(
                                    file_list=[
                                        dict(
                                            file_type='tar.gz',
                                            borkbork=True,
                                            ),
                                        dict(
                                            file_type='qcow2',
                                            build_serial='20120424',
                                            path=PATH,
                                            sha512=SHA512,
                                            ),
                                        ],
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        )
    got = discover.extract(catalog)
    assert got is not None
    assert got == dict(
        serial='20120424',
        url=URL,
        sha512=SHA512,
        )
