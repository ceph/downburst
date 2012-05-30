import hashlib
import libvirt
import logging
import requests

from lxml import etree

from . import discover
from . import exc
from . import template


log = logging.getLogger(__name__)


URLPREFIX = 'https://cloud-images.ubuntu.com/precise/current/'
URLNAME = 'precise-server-cloudimg-amd64-disk1.img'

PREFIX = 'precise-server-cloudimg-amd64-disk1.'
SUFFIX = '.img'


def list_cloud_images(pool):
    """
    List all Ubuntu 12.04 Cloud image in the libvirt pool.
    Return the keys.
    """
    for name in pool.listVolumes():
        log.debug('Considering image: %s', name)
        if not name.startswith(PREFIX):
            continue
        if not name.endswith(SUFFIX):
            continue
        if len(name) <= len(PREFIX) + len(SUFFIX):
            # no serial number in the middle
            continue
        # found one!
        log.debug('Saw image: %s', name)
        yield name


def find_cloud_image(pool):
    """
    Find an Ubuntu 12.04 Cloud image in the libvirt pool.
    Return the name.
    """
    names = list_cloud_images(pool)
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


def upload_volume(vol, fp, sha512):
    """
    Upload a volume into a libvirt pool.
    """

    h = hashlib.sha512()
    stream = vol.connect().newStream(flags=0)
    vol.upload(stream=stream, offset=0, length=0, flags=0)

    def handler(stream, nbytes, _):
        data = fp.read(nbytes)
        h.update(data)
        return data
    stream.sendAll(handler, None)

    if h.hexdigest() != sha512:
        stream.abort()
        raise exc.ImageHashMismatchError()
    stream.finish()


def ensure_cloud_image():
    """
    Ensure that the Ubuntu 12.04 Cloud image is in the libvirt pool.
    Returns the volume.
    """
    log.debug('Connecting to libvirt...')
    conn = libvirt.open('qemu:///system')
    if conn is None:
        raise exc.LibvirtConnectionError()

    log.debug('Opening libvirt pool...')
    pool = conn.storagePoolLookupByName('default')

    log.debug('Listing cloud image in libvirt...')
    name = find_cloud_image(pool=pool)
    if name is not None:
        # all done
        log.debug('Already have cloud image: %s', name)
        vol = pool.storageVolLookupByName(name)
        return vol

    log.debug('Discovering cloud images...')
    image = discover.get()

    log.debug('Will fetch serial number: %s', image['serial'])

    url = image['url']
    log.info('Downloading image: %s', url)
    r = requests.get(url)

    # volumes have no atomic completion marker; this will forever be
    # racy!
    name = '{prefix}{serial}{suffix}'.format(
        prefix=PREFIX,
        serial=image['serial'],
        suffix=SUFFIX,
        )
    log.debug('Creating libvirt volume: %s ...', name)
    volxml = template.volume(
        name=name,
        # TODO we really should feed in a capacity, but we don't know
        # what it should be.. libvirt pool refresh figures it out, but
        # that's probably expensive
        # capacity=2*1024*1024,
        )
    vol = pool.createXML(etree.tostring(volxml), flags=0)
    upload_volume(
        vol=vol,
        fp=r.raw,
        sha512=image['sha512'],
        )
    # TODO only here to autodetect capacity
    pool.refresh(flags=0)
    return vol
