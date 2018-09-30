import logging
import click

import platform

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
    'config': 'pyeye.ini'
}

defaults = windows_defaults
if platform.system() == 'Linux':
    defaults = linux_defaults

defaults.update(global_defaults)


@click.group()
@click.option('--loglevel', default='CRITICAL',
              type=click.Choice(LOG_LEVELS),
              help='python log levels')
@click.option('--logfile', default=defaults['logfile'], help="output log file")
@click.option('--color/--no-color', default=defaults['color'], help='Pretty color output')
@click.option('--config',
              default=defaults['config'], help='key/val (.ini) config file', callback=CLI.load_config)
@click.pass_context
def motion(ctx, loglevel, logfile, color, config):
    pass
