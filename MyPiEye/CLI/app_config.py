from os.path import exists
from os import environ
import configparser
import logging

log = logging.getLogger(__name__)


def load_config(ctx, param, config_filename):
    """
    Called by Click arg parser when an ini is passed in.

    Merges the [global] ini configuration with the cli flags,
    and adds sections from the ini file.

    Command-line parameters override .ini settings.

    Returns the config as a dict with the command line args as a [global] section

    :param ctx: Click context, the params attribute is used
    :param param: Click passes the parameter name, may be None
    :param config_filename: The ini file to process
    :return: The config as dict
    """

    log.info('loading config')
    ret = None

    # did we get a filename?
    if config_filename is not None:
        # does the config file exist?
        log.info('Reading config from {}'.format(config_filename))
        if exists(config_filename):
            ret = {}
            cfgparse = configparser.RawConfigParser()

            # load it
            cfgparse.read(config_filename)

            # load it all
            for sec in cfgparse.sections():
                ret[sec] = {}

                for key in cfgparse[sec]:
                    ret[sec][key] = cfgparse[sec][key]
        else:
            raise FileNotFoundError('{} was not found'.format(config_filename))

    global_settings = ret.get('global', None)
    if global_settings is None:
        log.warning('No [global] section found in .ini')
        ret['global'] = {}

    ret['global'].update(ctx.params)

    return ret


def get_config_value(
        config: dict,
        section_name: str,
        key_name: str,
        env_name: str = None,
        default=None):
    env_val = default
    section = config.get(section_name)
    if section is None:
        log.error('section {} not found'.format(section_name))
        return default

    if env_name is not None:
        env_val = environ.get(env_name)
        if env_val is None:
            return section.get(key_name, default)

    section[key_name] = env_val
    return env_val

def get_self_config_value(*args, **kwargs):
    log.error('******************************* DEPRECATED')
    raise NotImplementedError('this shouldn\'t be used')
