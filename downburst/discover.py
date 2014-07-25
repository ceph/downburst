import requests
import re
import csv
import HTMLParser
import json

URL="http://ceph.com/cloudinit/"

class Parser(HTMLParser.HTMLParser):
    def __init__(self):
        self.filenames = []
        HTMLParser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for key, val in attrs:
                if  key == 'href' and (val.endswith('.img') or val.endswith('.raw')):
                    self.filenames.append(val)

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
        '14.04': 'trusty'}

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

    def get_serial(self, release):
        url = self.URL + '/query/released.latest.txt'
        r = requests.get(url)
        r.raise_for_status()
        serial = None
        for row in csv.DictReader(r.content.strip().split("\n"),
                                  delimiter="\t",
                                  fieldnames=('release', 'flavour', 'stability',
                                              'serial')):

            if row['release'] == release and row['flavour'] == 'server':
                return row['serial'], row['stability']
        raise NameError('Image not found on server at ' + url)

    def get_filename(self, arch, version, state):
        if state == 'release':
            state = ''
        else:
            state = '-' + state
        return 'ubuntu-' + version + state + '-server-cloudimg-'+ arch + '-disk1.img'
        

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
        rows = csv.DictReader(r.content.strip().split("\n"), delimiter=" ",
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
        version = self.get_version(distroversion)
        serial, state = self.get_serial(release)
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
    parser.feed(r.content)
    parser.close()
    list = parser.filenames
    imageprefix = distro + '-' + distroversion + '-(\d+)'
    imagesuffix = '-cloudimg-' + arch + '.(img|raw)'
    imagestring = imageprefix + imagesuffix
    file = search(imagestring=imagestring, list=list)
    if file is not False:
        sha512 = requests.get(URL + file + ".sha512")
        sha512.raise_for_status()
        returndict = {}
        returndict['url'] = URL + "/" + file
        returndict['serial'] = file.split('-')[2]
        returndict['checksum'] = sha512.content.rstrip()
        returndict['hash_function'] = 'sha512'
        return returndict
    else:
        raise NameError('Image not found on server at ' + URL)

def add_distro(distro, version, distro_and_versions, codename=None):
    # Create dict entry for Distro, append if exists.
    if codename:
        version = '{version}({codename})'.format(version=version, codename=codename) 
    try:
        distro_and_versions[distro].append(version)
    except KeyError:
        distro_and_versions[distro] = [version]

def get_distro_list():
    ubuntu_url = 'http://cloud-images.ubuntu.com/query/released.latest.txt'
    distro_and_versions = {}

    # Non ubuntu distro's
    r = requests.get(URL)
    r.raise_for_status()

    # Pull .img filenames from HTML:
    parser = Parser()
    parser.feed(r.content)
    parser.close()
    for entry in parser.filenames:

        # Ignore Ubuntu (we dont pull those from ceph.com)
        if not entry.startswith('ubuntu'):

            #Ignore sha512 files
            if 'sha512' not in entry:
                if entry.endswith('.img') or entry.endswith('.raw'):

                    # Pull Distro and Version values from Filenames
                    distro = entry.split('-')[0]
                    version = '-'.join(re.split('[0-9]{8}', entry)[0].strip('-').split('-')[1:])
                    add_distro(distro, str(version), distro_and_versions)

    # Grab Ubuntu list from Ubuntu server:
    r = requests.get(ubuntu_url)
    r.raise_for_status()

    # Loop through latest codename list, convert to Version, add to dict.
    for line in r.content.rstrip().split('\n'):
        handler = UbuntuHandler()
        codename = line.split()[0]
        version = handler.get_version(codename)
        add_distro('ubuntu', version, distro_and_versions, codename)
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
    print json.dumps(get_distro_list())
    return

def print_distros(parser):
    distro_and_versions =get_distro_list()
    for distro in sorted(distro_and_versions):
        version = distro_and_versions[distro]
        print '{distro}:   \t {version}'. format(distro=distro,version=version)
    return

def search(imagestring, list):
    for imagename in list:
        if re.match(imagestring, imagename):
            return imagename
    return False
