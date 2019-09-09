import logging
import click
import sys
import platform

from functools import partial

import MyPiEye.CLI as CLI
from MyPiEye.main_app import MainApp
from MyPiEye.configure_app import ConfigureApp

from MyPiEye.multi.supervisor import Supervisor

import MyPiEye.CeleryTasks

# log = logging.getLogger('mypieye')
log = logging.getLogger(__name__)

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
@click.option('--logfile', default=None, help="output log file")
@click.option('--color/--no-color', default=None, help='Pretty color output')
@click.option('--iniconfig',
              default='mypieye.ini', help='key/val (.ini) config file', callback=CLI.load_config)
@click.pass_context
def mypieye(ctx, **cli_flags):
    log.info('Starting...')

    # the callback to the ``--iniconfig`` parameter updates
    # settings with the command line parameters
    ctx.obj = ctx.params['iniconfig']

    lvl = CLI.get_config_value(ctx.obj, 'global', 'loglevel', 'LOG_LEVEL')
    fmt = CLI.get_config_value(ctx.obj, 'global', 'log_format', 'LOG_FORMAT')
    CLI.enable_log(fmt=fmt)
    CLI.set_loglevel(lvl)


@mypieye.command()
@click.pass_context
def check(ctx, **cli_flags):
    print('Checking configuration.')

    config = ctx.obj

    config_app = ConfigureApp(config)

    if not config_app.check():
        log.critical('App configuration failed')
        sys.exit(-1)

    print('Configuration check passed')

    sys.exit(0)


@mypieye.command()
@click.pass_context
def configure(ctx, **cli_flags):
    print('Configuring...you may be prompted')

    config = ctx.obj

    config_app = ConfigureApp(config)

    if not config_app.configure():
        log.critical('Failed to configure app')
        sys.exit(-1)

    print('Application configured')

    if not config_app.check():
        log.critical('Start checks failed')
        sys.exit(-1)

    print('Start checks passed')


@mypieye.command(context_settings={"ignore_unknown_options": True})
@click.argument('appargs', nargs=-1)
@click.pass_context
def worker(ctx, appargs):
    """
    Accepts ``celery`` command line arguments, for example:

    ```
    python -m MyPiEye worker --pool=solo
    ```

    Use ``--pool=solo`` for debugging. Use ``--pool=eventlet`` to run on windows.

    :param ctx:
    :param appargs:
    :return:
    """
    config = ctx.obj
    config_app = ConfigureApp(config)
    if not config_app.check():
        log.critical('Start checks failed')
        sys.exit(-1)

    redis_cfg = partial(CLI.get_config_value, config, 'celery')
    redis_host = redis_cfg('host', 'CELERY_REDIS_HOST')
    redis_port = redis_cfg('port', 'CELERY_REDIS_PORT')
    redis_db = redis_cfg('db', 'CELERY_REDIS_DB')

    redis_url = f'redis://{redis_host}:{redis_port}/{redis_db}'
    MyPiEye.CeleryTasks.app_config = config

    MyPiEye.CeleryTasks.celery_app.conf.result_backend = redis_url
    MyPiEye.CeleryTasks.celery_app.conf.broker_url = redis_url
    args = ['worker'] + list(appargs)
    MyPiEye.CeleryTasks.celery_app.worker_main(args)


@mypieye.command()
@click.pass_context
def run(ctx, **cli_flags):
    log.warning('trying new mp framework')

    config = ctx.obj
    config_app = ConfigureApp(config)
    if not config_app.check():
        log.critical('Start checks failed')
        sys.exit(-1)

    sup = Supervisor(config)
    # blocks until return
    sup.start()

    sys.exit(0)


if __name__ == '__main__':
    mypieye()
