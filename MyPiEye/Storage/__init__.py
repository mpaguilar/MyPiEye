import multiprocessing
import logging
import signal
import sys

from MyPiEye.CLI import ColorLogFormatter

from .image_storage import ImageStorage
from .google_drive import GDriveStorage, GDriveAuth
from .local_filesystem import local_save

log_configured = False
mlogr = multiprocessing.get_logger()

if not log_configured:
    loghandler = logging.StreamHandler()
    logfmt = ColorLogFormatter('[%(asctime)s] [%(process)5s] %(levelname)s %(module)s %(name)s %(message)s')
    loghandler.setFormatter(logfmt)
    mlogr.addHandler(loghandler)
    log_configured = True


def clean_exit(sig, _):
    mlogr.critical('Program aborted with signal {}'.format(sig))
    sys.exit(sig)


signal.signal(signal.SIGINT, clean_exit)
