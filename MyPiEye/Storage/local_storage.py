from shutil import copyfile
from os.path import basename, exists, split
from os import makedirs, environ
from io import BytesIO

import cv2

from MyPiEye.CLI import get_self_config_value

import multiprocessing

log = multiprocessing.get_logger()


class LocalStorage(object):

    def __init__(self, config: dict):
        self.global_config = config
        self.self_config = config['local']

        self.savedir = get_self_config_value(self, 'savedir', 'LOCAL_SAVEDIR')
        self.static_web_dir = get_self_config_value(self, 'static_web_dir', 'LOCAL_STATIC')
        self.filename_format = get_self_config_value(self, 'filename_format', 'LOCAL_FMT')

    def upload(self, cv2_imgbuf, dt_stamp, camera_id):
        log.info('Uploading to file system {}')
        filename = '{}/{}.jpg'.format(camera_id, dt_stamp.strftime(self.filename_format))

        fdir, fname = split(filename)

        if not exists(fdir):
            log.info('Creating directory {}'.format(fdir))
            makedirs(fdir)

        ok = cv2.imwrite(filename)
        if not ok:
            log.error('Error writing file')
            return False

        return True

    def configure(self):
        if not exists(self.savedir):
            log.warning('FS: Creating save directory {}'.format(self.savedir))
            makedirs(self.savedir)

        return True

    def check(self):

        ok = True

        if self.savedir is None:
            log.error('FS: savedir is required')

        if not exists(self.savedir):
            log.error('FS: Save directory does not exist: {}'.format(self.savedir))
            ok = False

        return ok
