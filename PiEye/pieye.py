import logging
import click

import platform
from startup import Startup

import CLI

log = logging.getLogger(__name__)

windows_defaults = {
    'workdir': 'tmp',
    'savedir': 'c:/temp'
}

linux_defaults = {
    'workdir': '/tmp/snaps',
    'savedir': None
}

global_defaults = {
    'gdrive': 'ezmotion_test',
    'url': None,
    'camera': '0',
    'resolution': '720p',
    'show_timings': False,
    'logfile': None,
    'loglevel': 'DEBUG',
    'color': True,
    'config': 'pieye.ini'
}

defaults = windows_defaults
if platform.system() == 'Linux':
    defaults = linux_defaults

defaults.update(global_defaults)


@click.command()
@click.option('--loglevel', default='CRITICAL',
              type=click.Choice(CLI.LOG_LEVELS),
              help='python log levels')
@click.option('--logfile', default=defaults['logfile'], help="output log file")
@click.option('--color/--no-color', default=defaults['color'], help='Pretty color output')
@click.option('--config',
              default=defaults['config'], help='key/val (.ini) config file', callback=CLI.load_config)
@click.option('--workdir', default=defaults['workdir'], help='Temporary directory for processing images')
@click.option('--savedir', default=defaults['savedir'], help='Where to store files')
@click.option('--gdrive', default=defaults['gdrive'], help='Google drive folder')
@click.option('--camera', default=defaults['camera'], help='Camera to watch')
@click.option('--resolution', default=defaults['resolution'], type=click.Choice(['small', '720p', '1080p']),
              help='Camera resolution')
def motion(**config):
    """Start capturing and watching"""

    loglevel = config['loglevel']
    color = config['color']
    logfile = config['logfile']

    CLI.set_loglevel(loglevel)
    CLI.enable_log(filename=logfile, enable_color=color)
    log.info('Starting...')

    Startup(config)


if __name__ == '__main__':
    motion()

"""
 - check for directories
 - check camera
 - get first image
 - loop
   - get next image
   - compare with previous
     - diff image uploaded
       - google
       - local storage
"""