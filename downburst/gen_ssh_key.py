#!/usr/bin/python
import os
import shutil
import subprocess
import tempfile


def read_and_delete(parent, name):
    path = os.path.join(parent, name)
    with file(path, 'rb') as f:
        data = f.read()
    os.unlink(path)
    return data


def gen_ssh_key(args):
    tmp = tempfile.mkdtemp(
        prefix='downburst-ssh-keys.',
        suffix='.tmp',
        )
    keys = {}
    try:
        for key_type in ['rsa', 'dsa']:
            subprocess.check_call(
                args=[
                    'ssh-keygen',
                    '-q',
                    '-t', key_type,
                    '-N', '',
                    '-f', 'key',
                    ],
                cwd=tmp,
                close_fds=True,
                )
            keys.update(
                [
                    ('{t}_private'.format(t=key_type),
                     read_and_delete(tmp, 'key')),
                    ('{t}_public'.format(t=key_type),
                     read_and_delete(tmp, 'key.pub')),
                    ]
                )
        os.rmdir(tmp)
    except:
        shutil.rmtree(tmp)
        raise

    # yaml.safe_dump formats this ugly as hell, so do it manually
    print '#cloud-config-archive'
    print '- type: text/cloud-config'
    print '  content: |'
    print '    ssh_keys:'
    for k, v in sorted(keys.items()):
        print '      {0}: |'.format(k)
        for l in v.splitlines():
            print '        {0}'.format(l)


def make(parser):
    """
    Generate SSH host keys in a user-meta yaml format.
    """
    parser.set_defaults(func=gen_ssh_key)
