import requests
import json

BASE_URL = 'https://cloud-images.ubuntu.com/'
URL = BASE_URL + 'query2/ec2.json'


def extract(catalog, dist, ver):
    tag = "release"

    for distro in catalog['catalog']:
        if distro['distro_version'] != ver:
            continue
        for build in distro['build_types']['server']:
            if build['release_tag'] != tag:
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

def get(distro, distroversion):
    if distro == "ubuntu":
        catalog = fetch()
        return extract(catalog, dist=distro, ver=distroversion)
    else:
        raise NameError('Downloadiong of distributions other than Ubuntu not supported by downburst.')
        return None
