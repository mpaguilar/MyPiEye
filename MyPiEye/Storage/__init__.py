from .image_storage import ImageStorage
from .google_drive import GDriveStorage, GDriveAuth
from .local_filesystem import local_save

from MyPiEye.CLI import ColorLogFormatter
import logging
import multiprocessing


def get_logger():
    mlogr = multiprocessing.get_logger()
    loghandler = logging.StreamHandler()
    logfmt = ColorLogFormatter('[%(asctime)s] [%(process)5s] %(levelname)s %(module)s %(name)s %(message)s')
    loghandler.setFormatter(logfmt)
    mlogr.addHandler(loghandler)
    return mlogr


get_logger()
