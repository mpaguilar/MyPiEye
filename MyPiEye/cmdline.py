import logging
import click
import sys
import signal
import platform

import MyPiEye.CLI as CLI
from MyPiEye.main_app import MainApp
from MyPiEye.configure_app import ConfigureApp

log = logging.getLogger('mypieye')

windows_settings = {
    'savedir': 'c:/temp'
}

linux_settings = {
    'savedir': None
}

settings = {
    'camera': '0',
    'resolution': '720p',
    'show_timings': False,
    'logfile': None,
    'loglevel': 'DEBUG',
    'color': False,
    'config': 'mypieye.ini',
    'credential_folder': '.'
}

if platform.system() == 'Linux':
    settings.update(linux_settings)
else:
    settings.update(windows_settings)


def clean_exit(sig, _):
    log.critical('Program aborted with signal {}'.format(sig))
    sys.exit(sig)


@click.group()
@click.option('--loglevel', default='INFO',
              type=click.Choice(CLI.LOG_LEVELS),
              help='python log levels')
@click.option('--logfile', default=settings['logfile'], help="output log file")
@click.option('--color/--no-color', default=settings['color'], help='Pretty color output')
@click.option('--iniconfig',
              default=settings['config'], help='key/val (.ini) config file', callback=CLI.load_config)
@click.pass_context
def mypieye(ctx, **cli_flags):
    settings.update(ctx.params['iniconfig'])
    settings.update(cli_flags)
    del settings['iniconfig']

    ctx.params = dict(settings)

    CLI.set_loglevel(settings['loglevel'])
    if not CLI.enable_log(enable_color=settings['color']):
        log.critical('Error opening logger')
        sys.exit(-2)


@mypieye.command()
@click.pass_context
def check(ctx, **cli_flags):
    print('Checking configuration.')

    config = ConfigureApp(settings)

    if not config.check():
        log.critical('App configuration failed')
        sys.exit(-1)

    print('Configuration check passed')

    sys.exit(0)


@mypieye.command()
@click.pass_context
def configure(ctx, **cli_flags):
    print('Configuring...you may be prompted')

    config = ConfigureApp(settings)
    if not config.configure():
        log.critical('Failed to configure app')
        sys.exit(-1)

    print('Application configured')

    if not config.check():
        log.critical('Start checks failed')
        sys.exit(-1)

    print('Start checks passed')

@mypieye.command()
@click.pass_context
def s3_archive(ctx, **cli_flags):
    log.info('Archiving S3 objects')

    config = ConfigureApp(settings)

    # don't check the config, this may be run on a completely different machine
    mainapp = MainApp(settings)
    mainapp.s3_archive()

    log.info('Archive complete')


@mypieye.command()
@click.pass_context
def run(ctx, **cli_flags):
    """
    Start capturing and watching.
    Exit codes greater than zero are a command parsing error.
    Exit codes less than zero are from the app.
    """

    # handle Ctrl+C, so it doesn't give a stack dump.
    signal.signal(signal.SIGINT, clean_exit)

    log.info('Starting...')

    config = ConfigureApp(settings)
    if not config.check():
        log.critical('Start checks failed')
        sys.exit(-1)

    mainapp = MainApp(settings)

    if not mainapp.start():
        log.critical('Failed to start main app')
        sys.exit(-3)

    sys.exit(0)


if __name__ == '__main__':
    mypieye()
