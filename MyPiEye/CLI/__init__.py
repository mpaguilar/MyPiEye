import logging
from colorama import init, Fore, Back, Style
from os.path import exists, abspath
import configparser

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


def enable_log(fmt='[%(asctime)s] %(levelname)s %(module)s %(name)s %(message)s',
               enable_color=True, filename=None):
    """
    Clears all log handlers, and adds color handler and/or file handlers

    :param fmt: logging format string
    :param enable_color: True to enable
    :param filename: log file location
    :return: True
    """

    # if there's no special requirements for logging
    # we still want the formatting.
    if not enable_color and \
            filename is None and \
            filename != '':
        logging.basicConfig(format=fmt)
        return True

    lgr = logging.getLogger()
    lgr.handlers.clear()
    logfilename = abspath(filename)

    if enable_color:
        loghandler = logging.StreamHandler()
        logfmt = ColorLogFormatter(fmt)
        loghandler.setFormatter(logfmt)
        lgr.addHandler(loghandler)

    if filename is not None and filename != '':
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
            cfgparse = configparser.ConfigParser()

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

    ctx.params.update(ret['global'])
    del ret['global']

    return ret
