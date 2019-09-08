import logging
from colorama import init, Fore, Back, Style
from os.path import abspath

from .app_config import \
    load_config, \
    get_config_value, \
    get_self_config_value

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

    lgr = logging.getLogger()
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

