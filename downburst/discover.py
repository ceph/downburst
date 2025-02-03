import csv
import json
import logging
import os
import re
import requests

from html.parser import HTMLParser

log = logging.getLogger(__name__)

URL=os.environ.get("DOWNBURST_DISCOVER_URL", "http://download.ceph.com/cloudinit/")

class Parser(HTMLParser):
    def __init__(self):
        self.filenames = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, val in attrs:
                if  key == 'href' and (val.endswith('.img') or val.endswith('.raw')):
                    self.filenames.append(val)

class ReleaseParser(HTMLParser):
    def __init__(self):
        self.dirs = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, val in attrs:
                if  key == 'href' and val.startswith('release-'):
                    self.dirs.append(val.rstrip('/'))

class UbuntuVersionParser(HTMLParser):
    def __init__(self):
        self.versions = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            r = re.compile(r'^([0-9]+\.[0-9]+(?:\.[0-9]+)?)/')
            for key, val in attrs:
                if  key == 'href':
                    res = r.search(val)
                    if res:
                        self.versions.append(val.rstrip('/'))

class UbuntuHandler:
    URL = 'http://cloud-images.ubuntu.com'

    VERSION_TO_RELEASE = {
        '4.10': 'warty',
        '5.10': 'hoary',
        '5.10': 'breezy',
        '6.06': 'dapper',
        '6.10': 'edgy',
        '7.04': 'feisty',
        '7.10': 'gutsy',
        '8.04': 'hardy',
        '8.10': 'intrepid',
        '9.04': 'jaunty',
        '9.10': 'karmic',
        '10.04': 'lucid',
        '10.10': 'maverick',
        '11.04': 'natty',
        '11.10': 'oneiric',
        '12.04': 'precise',
        '12.10': 'quantal',
        '13.04': 'raring',
        '13.10': 'saucy',
        '14.04': 'trusty',
        '14.10': 'utopic',
        '15.04': 'vivid',
        '15.10': 'wily',
        '16.04': 'xenial',
        '18.04': 'bionic',
        '20.04': 'focal',
        '20.10': 'groovy',
        '21.04': 'hirsute',
        '21.10': 'impish',
        '22.04': 'jammy',
        '22.10': 'kinetic',
        '23.04': 'lunar',
        '23.10': 'mantic',
        '24.04': 'noble',
        '24.10': 'oracular',
    }

    RELEASE_TO_VERSION = {v:k for k, v in VERSION_TO_RELEASE.items()}


    def get_release(self, distroversion):
        try:
            if "." in distroversion:
                version = distroversion.split('.', 1)
                major = version[0]
                minor = version[1].split('.', 1)[0]
                return self.VERSION_TO_RELEASE[major + "." + minor]
        except KeyError:
            return distroversion

    def get_version(self, distroversion):
        try:
            return self.RELEASE_TO_VERSION[distroversion]
        except KeyError:
            pass
        return distroversion

    def get_latest_release_serial(self, release):
        url = self.URL + f"/releases/{release}"
        r = requests.get(url)
        r.raise_for_status()
        parser = ReleaseParser()
        parser.feed(r.content.decode())
        parser.close()
        latest_release_directory = sorted(parser.dirs)[-1]
        if latest_release_directory:
            serial = latest_release_directory.split('-')[1]
            return serial, 'release'

        raise NameError('Image not found on server at ' + url)

    def get_releases(self):
        """
        Returns dict version
        """
        url = f"{self.URL}/releases/"
        log.debug(f"Lookup for Ubuntu release by: {url}")
        r = requests.get(url)
        r.raise_for_status()
        parser = UbuntuVersionParser()
        parser.feed(r.content.decode())
        parser.close()
        version_release = {}
        for ver in parser.versions:
            v = ver.split(".")
            if len(v) > 1:
                major_minor = f"{v[0]}.{v[1]}"
                release = self.VERSION_TO_RELEASE.get(major_minor)
                if release:
                    version_release[ver] = release
        return version_release

    def get_filename(self, arch, version, state):
        if state == 'release':
            state = ''
        else:
            state = '-' + state
        major, minor = version.split('.')[0:2]
        if int(major) >= 23 and int(minor) >= 10:
            return 'ubuntu-' + major + '.' + minor + state + '-server-cloudimg-'+ arch + '.img'
        elif int(major) >= 20:
            return 'ubuntu-' + major + '.' + minor + state + '-server-cloudimg-'+ arch + '-disk-kvm.img'
        else:
            return 'ubuntu-' + major + '.' + minor + state + '-server-cloudimg-'+ arch + '-disk1.img'


    def get_base_url(self, release, serial, state):
        stability = ''
        added = 0
        for letter in state:
            if letter.isdigit() and added == 0:
                added=1
                stability += '-' + str(letter)
            else:
                stability += str(letter)

        if stability == 'release':
            location = stability + '-' + serial
        else:
            location = stability
        return self.URL + '/releases/' + release + '/' + location

    def get_url(self, base_url, filename):
        return base_url + "/" + filename

    def get_sha256(self, base_url, filename):
        url = base_url + "/SHA256SUMS"
        r = requests.get(url)
        rows = csv.DictReader(r.content.decode().strip().split("\n"), delimiter=" ",
                              fieldnames=('hash', 'file'))
        for row in rows:
            if row['file'] == "*" + filename:
                return row['hash']
        raise NameError('SHA-256 checksums not found for file ' + filename +
                        ' at ' + url)

    def __call__(self, distroversion, arch):
        distroversion = distroversion.lower()
        if arch == "x86_64":
            arch = "amd64"
        release = self.get_release(distroversion)
        log.debug(f"Found release: {release}")
        version = self.get_version(distroversion)
        serial, state = self.get_latest_release_serial(release)
        filename = self.get_filename(arch, version, state)
        base_url = self.get_base_url(release, serial, state)
        sha256 = self.get_sha256(base_url, filename)
        url = self.get_url(base_url, filename)

        return {'url': url, 'serial': serial, 'checksum': sha256,
                'hash_function': 'sha256'}

HANDLERS = {'ubuntu': UbuntuHandler()}

def get(distro, distroversion, arch):
    if distro in HANDLERS:
        handler = HANDLERS[distro]
        return handler(distroversion, arch)
    r = requests.get(URL)
    r.raise_for_status()
    parser = Parser()
    parser.feed(r.content.decode())
    parser.close()
    list = parser.filenames
    imageprefix = distro + '-' + distroversion + r'-(\d+)'
    imagesuffix = '-cloudimg-' + arch + '.(img|raw)'
    imagestring = imageprefix + imagesuffix
    file = search(imagestring=imagestring, list=list)
    if file is not False:
        sha512 = requests.get(URL + file + ".sha512")
        sha512.raise_for_status()
        returndict = {}
        returndict['url'] = URL + "/" + file
        returndict['serial'] = file.split('-')[2]
        returndict['checksum'] = sha512.content.decode().rstrip()
        returndict['hash_function'] = 'sha512'
        return returndict
    else:
        raise NameError('Image %s not found on server at %s' % (imagestring, URL))

def add_distro(distro, version, distro_and_versions, codename=None):
    # Create dict entry for Distro, append if exists.
    if codename:
        version = '{version}({codename})'.format(version=version, codename=codename)
    try:
        distro_and_versions[distro].append(version)
    except KeyError:
        distro_and_versions[distro] = [version]

def get_distro_list():
    distro_and_versions = {}

    # Non ubuntu distro's
    log.debug(f"Lookup images at {URL}")
    r = requests.get(URL)
    r.raise_for_status()

    # Pull .img filenames from HTML:
    parser = Parser()
    parser.feed(r.content.decode())
    parser.close()
    for entry in parser.filenames:
        distro,_ = entry.split('-', 1)
        # Ignore Ubuntu (we dont pull those from ceph.com)
        if not distro in HANDLERS.keys():

            #Ignore sha512 files
            if 'sha512' not in entry:
                if entry.endswith('.img') or entry.endswith('.raw'):

                    # Pull Distro and Version values from Filenames
                    version = '-'.join(re.split('[0-9]{8}', entry)[0].strip('-').split('-')[1:])
                    add_distro(distro, str(version), distro_and_versions)

    for distro, handler in HANDLERS.items():
        handler = UbuntuHandler()
        for version, codename in handler.get_releases().items():
            add_distro(distro, version, distro_and_versions, codename)
    return distro_and_versions

def make(parser):
    """
    Print Available Distributions and Versions.
    """
    parser.set_defaults(func=print_distros)

def make_json(parser):
    """
    Get json formatted distro and version information.
    """
    parser.set_defaults(func=print_json)

def print_json(parser):
    print(json.dumps(get_distro_list()))
    return

def print_distros(parser):
    distro_and_versions =get_distro_list()
    for distro in sorted(distro_and_versions):
        version = distro_and_versions[distro]
        print('{distro}:   \t {version}'. format(distro=distro,version=version))
    return

def search(imagestring, list):
    for imagename in list:
        if re.match(imagestring, imagename):
            return imagename
    return False
