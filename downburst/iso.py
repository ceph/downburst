import os
import os.path
import subprocess
import tempfile
import yaml

from lxml import etree

from . import template


def get_ssh_pubkey():
    path = os.path.expanduser('~/.ssh/id_rsa.pub')
    with file(path, 'rb') as f:
        return f.readline().rstrip('\n')


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
    with gentemp('meta') as meta, gentemp('user') as user:
        meta_data = {
            'instance-id': name,
            'local-hostname': name,
            'public-keys': [],
            }
        ssh_pubkey = get_ssh_pubkey()
        meta_data['public-keys'].append(ssh_pubkey)

        if extra_meta is not None:
            with file(extra_meta) as f:
                extra_meta_data = yaml.safe_load(f)
                meta_data.update(extra_meta_data)

        yaml.safe_dump(
            stream=meta,
            data=meta_data,
            default_flow_style=False,
            )
        meta.flush()

        user.write('#cloud-config-archive\n')
        user_data = [
            ]

        if extra_user is not None:
            with file(extra_user) as f:
                if f.readline() == '#cloud-config-archive\n':
                    # merge it into ours
                    extra_user_data = yaml.safe_load(f)
                    user_data.extend(extra_user_data)
                else:
                    # some other format; slap it in as a single string
                    f.seek(0)
                    extra_user_data = f.read()
                    user_data.append(extra_user_data)

        cloud_config = {}
        user_data.append(dict(
                type='text/cloud-config',
                content=yaml.safe_dump(
                    cloud_config,
                    default_flow_style=False,
                    ),
                ))
        yaml.safe_dump(
            stream=user,
            data=user_data,
            default_flow_style=False,
            )
        user.flush()

        subprocess.check_call(
            args=[
                'genisoimage',
                '-quiet',
                '-input-charset', 'utf-8',
                '-volid', 'cidata',
                '-joliet',
                '-rock',
                '-graft-points',
                'user-data={path}'.format(path=user.name),
                'meta-data={path}'.format(path=meta.name),
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
