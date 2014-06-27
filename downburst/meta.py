import logging
import os.path
import yaml
import requests
log = logging.getLogger(__name__)

def get_ssh_pubkey():
    path = os.path.expanduser('~/.ssh/id_rsa.pub')
    if not os.path.exists(path):
        log.warn("Public key not found, skipping it: " + path)
        return
    with file(path, 'rb') as f:
        return f.readline().rstrip('\n')


KEYURL='http://ceph.com/git/?p=keys.git;a=blob_plain;f=ssh/teuthology-ubuntu.pub;hb=HEAD'

def keyfetch():
    print "Fetching default SSH key from "+KEYURL
    r = requests.get(KEYURL)
    r.raise_for_status()
    gitkey = r.content
    if "ssh-" in gitkey:
        return gitkey
    else:
        raise Exception(KEYURL+" does not appear to contain an SSH key.")

def gen_meta(
    name,
    extra_meta,
    nokey,
    ):
    meta_data = {
        'instance-id': name,
        'local-hostname': name,
        'public-keys': [],
        }
    ssh_pubkey = get_ssh_pubkey()
    if ssh_pubkey is not None:
        meta_data['public-keys'].append(ssh_pubkey)

    if not nokey:
        ssh_gitkey = keyfetch()
        meta_data['public-keys'].append(ssh_gitkey)

    for path in extra_meta:
        with file(path) as f:
            extra_meta_data = yaml.safe_load(f)
            if extra_meta_data is not None:
                meta_data.update(extra_meta_data)

    return meta_data


def write_meta(meta_data, fp):
    yaml.safe_dump(
        stream=fp,
        data=meta_data,
        default_flow_style=False,
        )
    fp.flush()


def gen_user(
    name,
    extra_user,
    ):
    user_data = [
        ]

    for path in extra_user:
        with file(path) as f:
            if f.readline() == '#cloud-config-archive\n':
                # merge it into ours
                extra_user_data = yaml.safe_load(f)
                if extra_user_data is not None:
                    user_data.extend(extra_user_data)
            else:
                # some other format; slap it in as a single string
                f.seek(0)
                extra_user_data = f.read()
                user_data.append(extra_user_data)

    return user_data


def write_user(user_data, fp):
    fp.write('#cloud-config-archive\n')
    yaml.safe_dump(
        stream=fp,
        data=user_data,
        default_flow_style=False,
        )
    fp.flush()
