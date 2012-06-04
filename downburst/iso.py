import os
import subprocess
import tempfile

from lxml import etree

from . import meta
from . import template


def generate_meta_iso(
    name,
    fp,
    extra_meta=None,
    extra_user=None,
    ):
    def gentemp(prefix):
        return tempfile.NamedTemporaryFile(
            prefix='downburst.{prefix}.'.format(prefix=prefix),
            suffix='.tmp',
            )
    with gentemp('meta') as meta_f, gentemp('user') as user_f:
        meta_data = meta.gen_meta(name=name, extra_meta=extra_meta)
        meta.write_meta(meta_data=meta_data, fp=meta_f)

        user_data = meta.gen_user(name=name, extra_user=extra_user)
        meta.write_user(user_data=user_data, fp=user_f)

        subprocess.check_call(
            args=[
                'genisoimage',
                '-quiet',
                '-input-charset', 'utf-8',
                '-volid', 'cidata',
                '-joliet',
                '-rock',
                '-graft-points',
                'user-data={path}'.format(path=user_f.name),
                'meta-data={path}'.format(path=meta_f.name),
                ],
            stdout=fp,
            close_fds=True,
            )


def upload_volume(vol, length, fp):
    # TODO share with image.upload_volume
    stream = vol.connect().newStream(flags=0)
    vol.upload(stream=stream, offset=0, length=length, flags=0)

    def handler(stream, nbytes, _):
        data = fp.read(nbytes)
        return data
    stream.sendAll(handler, None)
    stream.finish()


def create_meta_iso(
    pool,
    name,
    extra_meta=None,
    extra_user=None,
    ):
    with tempfile.TemporaryFile() as iso:
        generate_meta_iso(
            name=name,
            fp=iso,
            extra_meta=extra_meta,
            extra_user=extra_user,
            )
        iso.seek(0)
        length = os.fstat(iso.fileno()).st_size
        assert length > 0
        volxml = template.volume(
            name='cloud-init.{name}.iso'.format(name=name),
            capacity=length,
            format_='raw',
            )
        vol = pool.createXML(etree.tostring(volxml), flags=0)
        upload_volume(
            vol=vol,
            length=length,
            fp=iso,
            )
        return vol
