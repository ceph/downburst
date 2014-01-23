import hashlib
import logging
import requests

from lxml import etree

from . import discover
from . import exc
from . import template

log = logging.getLogger(__name__)

def list_cloud_images(pool, distro, distroversion, arch):
    """
    List all Cloud images in the libvirt pool.
    Return the keys.
    """

    #Fix distro version if someone did not use quotes
    if distro == "ubuntu":
        if isinstance(distroversion, float):
            distroversion = '%.2f' % distroversion

    PREFIX = distro+"-"+distroversion+"-"
    SUFFIX = '-cloudimg-'+arch+'.img'
    SUFFIXRAW = '-cloudimg-'+arch+'.raw'

    for name in pool.listVolumes():
        log.debug('Considering image: %s', name)
        if not name.startswith(PREFIX):
            continue
        if not (name.endswith(SUFFIX) or name.endswith(SUFFIXRAW)):
            continue
        if len(name) <= len(PREFIX) + len(SUFFIX):
            # no serial number in the middle
            continue
        # found one!
        log.debug('Saw image: %s', name)
        yield name


def find_cloud_image(pool, distro, distroversion, arch):
    """
    Find a Cloud image in the libvirt pool.
    Return the name.
    """
    names = list_cloud_images(pool, distro=distro, distroversion=distroversion, arch=arch)
    # converting into a list because max([]) raises ValueError, and we
    # really don't want to confuse that with exceptions from inside
    # the generator
    names = list(names)

    if not names:
        log.debug('No cloud images found.')
        return None

    # the build serial is zero-padded, hence alphabetically sortable;
    # max is the latest image
    return max(names)


def upload_volume(vol, fp, hash_function, checksum):
    """
    Upload a volume into a libvirt pool.
    """

    h = hashlib.new(hash_function)
    stream = vol.connect().newStream(flags=0)
    vol.upload(stream=stream, offset=0, length=0, flags=0)

    def handler(stream, nbytes, _):
        data = fp.read(nbytes)
        h.update(data)
        return data
    stream.sendAll(handler, None)

    if h.hexdigest() != checksum:
        stream.abort()
        raise exc.ImageHashMismatchError()
    stream.finish()


def ensure_cloud_image(pool, distro, distroversion, arch, forcenew=False):
    """
    Ensure that the Ubuntu Cloud image is in the libvirt pool.
    Returns the volume.
    """

    log.debug('Listing cloud image in libvirt...')
    name = find_cloud_image(pool=pool, distro=distro, distroversion=distroversion, arch=arch)
    raw = False
    if not forcenew:
        if name is not None:
            # all done
            if name.endswith('.raw'):
                raw = True
            log.debug('Already have cloud image: %s', name)
            vol = pool.storageVolLookupByName(name)
            return vol, raw

    log.debug('Discovering cloud images...')
    image = discover.get(distro=distro, distroversion=distroversion, arch=arch)
    log.debug('Will fetch serial number: %s', image['serial'])

    url = image['url']
    if url.endswith('.raw'):
        raw = True
    log.info('Downloading image: %s', url)

    # prefetch used to default to False; 0.13.6 changed that to True, and
    # 1.0.0 changed it to 'stream' with the opposite sense.  We really
    # want streaming behavior no matter which version of requests; try
    # to cope with any version.
    if tuple(map(int, requests.__version__.split('.'))) < (1,0,0):
        r = requests.get(url, prefetch=False)
    else:
        r = requests.get(url, stream=True)

    # volumes have no atomic completion marker; this will forever be
    # racy!
    ext = '.img'
    if raw:
        ext = '.raw'
    PREFIX = distro+"-"+distroversion+"-"
    SUFFIX = '-cloudimg-'+arch+ext

    name = '{prefix}{serial}{suffix}'.format(
        prefix=PREFIX,
        serial=image['serial'],
        suffix=SUFFIX,
        )
    log.debug('Creating libvirt volume: %s ...', name)
    volxml = template.volume(
        name=name,
        raw=raw,
        # TODO we really should feed in a capacity, but we don't know
        # what it should be.. libvirt pool refresh figures it out, but
        # that's probably expensive
        # capacity=2*1024*1024,
        )
    vol = pool.createXML(etree.tostring(volxml), flags=0)
    upload_volume(
        vol=vol,
        fp=r.raw,
        hash_function=image['hash_function'],
        checksum=image['checksum'],
        )
    # TODO only here to autodetect capacity
    pool.refresh(flags=0)
    return vol, raw

