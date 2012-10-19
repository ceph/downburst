import requests
import json


BASE_URL = 'https://cloud-images.ubuntu.com/'
URL = BASE_URL + 'query2/ec2.json'


def extract(catalog):
    for distro in catalog['catalog']:
        if distro['distro_code_name'] != 'precise':
            continue
        for build in distro['build_types']['server']:
            if build['release_tag'] != 'release':
                continue
            arch = build['arches']['amd64']

            for image in arch['file_list']:
                if image['file_type'] != 'qcow2':
                    continue
                return dict(
                    serial=build['build_serial'],
                    url=BASE_URL + image['path'],
                    sha512=image['sha512'],
                    )


def fetch():
    r = requests.get(URL)
    r.raise_for_status()
    try:
        catalog = r.json
    except AttributeError:
        catalog = json.loads(r.content)
    return catalog


def get():
    catalog = fetch()
    return extract(catalog)
