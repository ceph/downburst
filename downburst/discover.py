import requests
import re

URL="http://ceph.com/cloudinit/"

def get(distro, distroversion, arch):
    r = requests.get(URL)
    r.raise_for_status()
    c = re.sub('.*a href="', '', r.content)
    content = re.sub('.img">.*', '.img', c)
    list = re.findall('.*-cloudimg-.*', content)
    imageprefix = distro + '-' + distroversion + '-(\d+)'
    imagesuffix = '-cloudimg-' + arch + '.img'
    imagestring = imageprefix + imagesuffix
    file = search(imagestring=imagestring, list=list)
    if file is not False:
        sha512 = requests.get(URL + file + ".sha512")
        sha512.raise_for_status()
        returndict = {}
        returndict['url'] = URL + "/" + file
        returndict['serial'] = file.split('-')[2]
        returndict['sha512'] = sha512.content.rstrip()
        return returndict
    else:
        raise NameError('Image not found on server at ' + URL)

def search(imagestring, list):
    for imagename in list:
        if re.match(imagestring, imagename):
            return imagename
    return False
