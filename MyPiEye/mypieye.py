import logging
import click
import sys

import platform

import CLI
from main_app import MainApp

log = logging.getLogger(__name__)

windows_settings = {
    'workdir': 'c:/temp',
    'savedir': 'c:/temp'
}

linux_settings = {
    'workdir': '/tmp/snaps',
    'savedir': None
}

global_settings = {
    'gdrive': None,
    'camera': '0',
    'resolution': '720p',
    'show_timings': False,
    'logfile': None,
    'loglevel': 'DEBUG',
    'color': False,
    'config': 'mypieye.ini'
}

settings = windows_settings
if platform.system() == 'Linux':
    defaults = linux_settings

settings.update(global_settings)


@click.command()
@click.option('--loglevel', default='CRITICAL',
              type=click.Choice(CLI.LOG_LEVELS),
              help='python log levels')
@click.option('--logfile', default=settings['logfile'], help="output log file")
@click.option('--color/--no-color', default=settings['color'], help='Pretty color output')
@click.option('--iniconfig',
              default=settings['config'], help='key/val (.ini) config file', callback=CLI.load_config)
def mypieye(**cli_flags):
    """Start capturing and watching"""

    settings.update(cli_flags)

    # let's just assume these are okay
    loglevel = settings['loglevel']
    color = settings['color']
    logfile = settings['logfile']

    CLI.set_loglevel(loglevel)
    if not CLI.enable_log(filename=logfile, enable_color=color):
        log.error('Error opening logger')
        sys.exit(1)

    log.info('Starting...')

    mainapp = MainApp(settings)
    if not mainapp.check():
        log.critical('Start checks failed')
        sys.exit(2)

    mainapp.start()
    sys.exit(0)


if __name__ == '__main__':
    mypieye()
