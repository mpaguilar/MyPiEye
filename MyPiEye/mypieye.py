import logging
import click
import sys

import platform

import CLI
from MainApp import MainApp

log = logging.getLogger(__name__)

windows_defaults = {
    'workdir': 'c:/temp',
    'savedir': 'c:/temp'
}

linux_defaults = {
    'workdir': '/tmp/snaps',
    'savedir': None
}

global_defaults = {
    'gdrive': None,
    'url': None,
    'camera': '0',
    'resolution': '720p',
    'show_timings': False,
    'logfile': None,
    'loglevel': 'DEBUG',
    'color': True,
    'config': 'mypieye.ini'
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
def mypieye(**gconfig):
    """Start capturing and watching"""

    # let's just assume these are okay
    loglevel = gconfig['loglevel']
    color = gconfig['color']
    logfile = gconfig['logfile']

    CLI.set_loglevel(loglevel)
    CLI.enable_log(filename=logfile, enable_color=color)
    log.info('Starting...')

    mainapp = MainApp(gconfig)
    if not mainapp.check():
        log.critical('Start checks failed')
        sys.exit(1)

    mainapp.start()
    sys.exit(0)


if __name__ == '__main__':
    mypieye()
