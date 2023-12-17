import os
import secrets
import string


def put(c, local_path, remote_path, permissions=None, owner='root', group=None):
    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    c.put(local_path, tmp_path)

    if is_dir(c, remote_path):
        if not remote_path.endswith('/'):
            remote_path += '/'

        filename = os.path.basename(local_path)
        remote_path += filename

    c.sudo(f"mv '{tmp_path}' '{remote_path}'")
    c.sudo(f"rm -rf '{tmp_path}'")

    set_permission(c, remote_path, permissions=permissions, owner=owner, group=group)


def put_str(c, remote_path, str_):
    tmp_file = 'tmp.txt'
    with open(tmp_file, 'w') as outfile:
        outfile.write(str_ + '\n')
    put(c, tmp_file, remote_path)
    os.remove(tmp_file)


def append_str(c, remote_path, str_):
    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    put_str(c, tmp_path, str_)

    sudo_cmd(c, f"cat '{tmp_path}' >> '{remote_path}'")
    c.sudo(f'rm -f {tmp_path}')


def sudo_cmd(c, cmd, user=None):
    cmd = cmd.replace('"', '\\"')
    c.sudo(f'bash -c "{cmd}"', user=user)


def set_permission(c, path, *, permissions=None, owner=None, group=None):
    if owner:
        if not group:
            group = owner
        c.sudo(f"chown {owner}:{group} '{path}'")

    if permissions:
        c.sudo(f"chmod {permissions} '{path}'")


def reboot(c):
    print('Rebooting')
    try:
        c.sudo('reboot')
    except Exception:
        pass


def exists(c, path):
    return c.sudo(f"test -e '{path}'", hide=True, warn=True).ok


def is_dir(c, path):
    return c.sudo(f"test -d '{path}'", hide=True, warn=True).ok


def random_string(length):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def ubuntu_release(c):
    return c.run('lsb_release -rs').stdout.strip()[:2]


def ubuntu_codename(c):
    return c.run('lsb_release -cs').stdout.strip()


def apt_get_update(c):
    c.sudo('apt-get update')


def apt_get_install(c, pkgs, warn=False):
    c.sudo(
        f'DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {pkgs}',
        warn=warn,
        echo=True,
    )


def apt_get_purge(c, pkgs):
    c.sudo(f'DEBIAN_FRONTEND=noninteractive apt-get purge -y {pkgs}')


def apt_get_autoremove(c):
    c.sudo('DEBIAN_FRONTEND=noninteractive apt-get autoremove -y')


def get_username(c):
    return c.run('whoami').stdout.strip()


def add_user(c, username, passwd=None, uid=None):
    uid_str = f'--uid={uid}' if uid else ''

    # --disabled-password - ssh-key login only
    c.sudo(f'adduser --disabled-password --gecos "" {uid_str} {username}', warn=True)
    if passwd:
        sudo_cmd(c, f'echo "{username}:{passwd}" | chpasswd')


def remove_user(c, username):
    c.sudo(f'userdel -r {username}', warn=True)
    c.sudo(f'rm -rf /home/{username}')


def enable_sudo(c, username, nopasswd=False):
    c.sudo(f'usermod -aG sudo {username}')
    if nopasswd:
        put_str(c, '/etc/sudoers.d/tmp.', f'{username} ALL=(ALL) NOPASSWD:ALL')
        set_permission(c, '/etc/sudoers.d/tmp.', permissions='440', owner='root')
        c.sudo(f'mv /etc/sudoers.d/tmp. /etc/sudoers.d/{username}')


def ssh_copy_id(c, username, key_file_path):
    with open(key_file_path) as fp:
        public_key_str = fp.read()

    if username == 'root':
        home_dir = '/root'
    else:
        home_dir = f'/home/{username}'

    ssh_dir = f'{home_dir}/.ssh'

    c.sudo(f'mkdir -p {ssh_dir}')
    c.sudo(f'chown {username}:{username} {ssh_dir}')

    put_str(c, f'{ssh_dir}/authorized_keys', public_key_str)
    set_permission(c, f'{ssh_dir}/authorized_keys', permissions='400', owner=username)


def setup_time(c):
    apt_get_install(c, 'dbus')

    c.sudo('timedatectl set-local-rtc 0')
    c.sudo('timedatectl set-ntp 1')
    c.sudo('timedatectl set-timezone UTC')