import logging
import click
import sys
import signal
import platform

import MyPiEye.CLI as CLI
from MyPiEye.main_app import MainApp
from MyPiEye.configure_app import ConfigureApp

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
    'config': 'mypieye.ini',
    'credential_folder': '.'
}

settings = windows_settings
if platform.system() == 'Linux':
    defaults = linux_settings

settings.update(global_settings)


def clean_exit(sig, _):
    log.critical('Program aborted with signal {}'.format(sig))
    sys.exit(0)


@click.group()
def mypieye():
    pass


@mypieye.command()
@click.option('--iniconfig',
              default=settings['config'], help='key/val (.ini) config file', callback=CLI.load_config)
def configure(**cli_flags):
    settings.update(cli_flags)


    color = settings['color']

    CLI.set_loglevel('INFO')
    if not CLI.enable_log(enable_color=color):
        log.critical('Error opening logger')
        sys.exit(-2)

    config = ConfigureApp(settings)
    if not config.initialize():
        log.critical('Failed to configure app')
        sys.exit(-1)

    if not config.check():
        log.critical('Start checks failed')
        sys.exit(-1)


@mypieye.command()
@click.option('--loglevel', default='INFO',
              type=click.Choice(CLI.LOG_LEVELS),
              help='python log levels')
@click.option('--logfile', default=settings['logfile'], help="output log file")
@click.option('--color/--no-color', default=settings['color'], help='Pretty color output')
@click.option('--iniconfig',
              default=settings['config'], help='key/val (.ini) config file', callback=CLI.load_config)
def run(**cli_flags):
    """
    Start capturing and watching.
    Exit codes greater than zero are a command parsing error.
    Exit codes less than zero are from the app.
    """

    # handle Ctrl+C, so it doesn't give a stack dump.
    signal.signal(signal.SIGINT, clean_exit)

    settings.update(cli_flags)

    # let's just assume these are okay
    loglevel = settings['loglevel']
    color = settings['color']
    logfile = settings['logfile']

    CLI.set_loglevel(loglevel)
    if not CLI.enable_log(filename=logfile, enable_color=color):
        log.critical('Error opening logger')
        sys.exit(-2)

    log.info('Starting...')

    mainapp = MainApp(settings)

    if not mainapp.start():
        log.critical('Failed to start main app')
        sys.exit(-3)

    sys.exit(0)


mypieye()
