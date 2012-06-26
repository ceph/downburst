import os.path
import yaml


def get_ssh_pubkey():
    path = os.path.expanduser('~/.ssh/id_rsa.pub')
    with file(path, 'rb') as f:
        return f.readline().rstrip('\n')


def gen_meta(
    name,
    extra_meta,
    ):
    meta_data = {
        'instance-id': name,
        'local-hostname': name,
        'public-keys': [],
        }
    ssh_pubkey = get_ssh_pubkey()
    meta_data['public-keys'].append(ssh_pubkey)

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
