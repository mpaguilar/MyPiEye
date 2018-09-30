import logging
from colorama import init, Fore, Back, Style
from os.path import exists
import configparser

init()

logging.getLogger(__name__)


class ColorLogFormatter(logging.Formatter):
    def __init__(self, log_format):
        super().__init__(log_format)

    def format(self, record):
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
            sup = " *** " + sup + " *** "

        return fore + sup + Fore.RESET + Style.RESET_ALL


LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def enable_log(fmt='[%(asctime)s] %(levelname)s %(module)s %(message)s',
               enable_color=True, filename=None):
    """
    Clears all log handlers, and adds color handler and/or file handlers
    :param fmt: logging format string
    :param enable_color: True to enable
    :param filename: log file location
    :return: True
    """
    lgr = logging.getLogger()
    lgr.handlers.clear()

    if enable_color:
        loghandler = logging.StreamHandler()
        logfmt = ColorLogFormatter(fmt)
        loghandler.setFormatter(logfmt)
        lgr.addHandler(loghandler)

    if filename is not None:
        fhandler = logging.FileHandler(filename)
        logfmt = logging.Formatter(fmt)
        fhandler.setFormatter(logfmt)
        lgr.addHandler(fhandler)

    return True


def set_loglevel(level_str):
    """
    Converts a string into a logging level, and sets it accordingly
    :param level_str:
    :return: True
    """
    lgr = logging.getLogger()
    lgr.setLevel(LOG_LEVELS[level_str])
    return True


def load_config(ctx, param, config_filename):
    """
    Called by Click arg parser when an ini is passed in. It doesn't use any Click variables, and
    can be used for any ini file. Returns the config as a dict.
    :param ctx: Click context, may be None
    :param param: Click passes the parameter name, may be None
    :param config_filename: The ini file to process
    :return: The config as dict
    """

    log.info('loading config')
    ret = None

    # did we get a filename?
    if config_filename is not None:
        # does the config file exist?
        if exists(val):
            log.info('Reading config from {}'.format(val))
            ret = {}
            p = configparser.ConfigParser()

            # load it
            p.read(val)

            # load it all
            for sec in p.sections():
                ret[sec] = {}

                for key in p[sec]:
                    ret[sec][key] = p[sec][key]

    return ret
