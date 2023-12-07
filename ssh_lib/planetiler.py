from ssh_lib.utils import apt_get_install, apt_get_update


PLANETILER_VERSION = '0.7.0'

PLANETILER_DIR = '/data/planetiler/bin'
PLANETILER_PATH = f'{PLANETILER_DIR}/planetiler.jar'


def install_planetiler(c):
    apt_get_update(c)
    apt_get_install(c, 'openjdk-17-jdk')

    c.sudo('mkdir -p /data/planetiler/bin')

    c.sudo(
        f'wget -q https://github.com/onthegomap/planetiler/releases/download/v{PLANETILER_VERSION}/planetiler.jar '
        f'-O {PLANETILER_PATH}',
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help')

    c.sudo('chown -R ofm:ofm /data/planetiler')
