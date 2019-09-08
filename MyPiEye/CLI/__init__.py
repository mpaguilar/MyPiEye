import logging
from colorama import init, Fore, Back, Style
from os.path import exists, abspath
from os import environ
import configparser
import multiprocessing

init()

log = logging.getLogger(__name__)


class ColorLogFormatter(logging.Formatter):
    def __init__(self, log_format):
        """

        :param log_format: %s-formatted
        """
        super().__init__(log_format)

    def format(self, record):
        """
        Adds color to log output.

        :param record: logging record object
        :return: formatted text
        """
        sup = super().format(record)
        fore = Fore.RESET

        if 0 == record.levelno:
            return sup

        if 10 == record.levelno:
            fore = Fore.GREEN

        if 20 == record.levelno:
            fore = Fore.CYAN

        if 30 == record.levelno:
            fore = Style.BRIGHT + Fore.YELLOW

        if 40 == record.levelno:
            fore = Fore.RED

        if 50 == record.levelno:
            fore = Back.RED + Fore.BLACK
            # sup = " *** " + sup + " *** "

        return fore + sup + Fore.RESET + Style.RESET_ALL


LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def enable_log(fmt='[%(asctime)s] [%(process)5s] %(levelname)s %(module)s %(name)s %(message)s',
               enable_color=True, filename=None):
    """
    Clears all log handlers, and adds color handler and/or file handlers

    :param fmt: logging format string
    :param enable_color: True to enable
    :param filename: log file location
    :return: Logger object
    """

    # lgr = logging.getLogger()
    lgr = multiprocessing.get_logger()
    lgr.handlers.clear()

    # if there's no special requirements for logging
    # we still want the formatting.
    if not enable_color and \
            filename is None and \
            filename != '':
        loghandler = logging.StreamHandler()
        logfmt = logging.Formatter(fmt)
        loghandler.setFormatter(logfmt)
        lgr.addHandler(loghandler)
        return True

    if enable_color:
        loghandler = logging.StreamHandler()
        logfmt = ColorLogFormatter(fmt)
        loghandler.setFormatter(logfmt)
        lgr.addHandler(loghandler)

    if filename is not None and filename != '':
        logfilename = abspath(filename)
        fhandler = logging.FileHandler(logfilename)
        logfmt = logging.Formatter(fmt)
        fhandler.setFormatter(logfmt)
        lgr.addHandler(fhandler)

    return True


def set_loglevel(level_str):
    """
    Converts a string into a logging level, and sets it accordingly

    :param level_str: 'DEBUG', 'WARN', etc.
    :return: True
    """
    lgr = logging.getLogger()
    lgr.setLevel(LOG_LEVELS[level_str])
    return True


def load_config(ctx, param, config_filename):
    """
    Called by Click arg parser when an ini is passed in.

    Merges the [global] ini configuration with the cli flags,
    and adds sections from the ini file.

    Returns the config as a dict.

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

    ret.update(ret['global'])
    del ret['global']
    # ctx.params = ret

    return ret


def get_self_config_value(obj, key_name, env_name, default=None):
    """
    If the environment variable is found, the config
    object will be updated with it's value
    :param obj: should have a member named ``self_config``.
    :param key_name:
    :param env_name:
    :param default:
    :return:
    """
    val = environ.get(env_name)
    if val is None:
        val = obj.self_config.get(key_name, default)
    else:
        obj.self_config[key_name] = val

    return val


def get_config_value(
        config: dict,
        section_name: str,
        key_name: str,
        env_name: str = None,
        default=None):
    env_val = default

    if config is None:
        log.error('No config passed')
        return default

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
