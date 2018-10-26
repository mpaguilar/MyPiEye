from shutil import copyfile
from os.path import basename, exists
from os import makedirs
import logging

import multiprocessing

from MyPiEye.motion_detect import ImageCapture

log = multiprocessing.get_logger()


class FileStorage(object):

    def __init__(self, config: dict):
        pass
        self.config = config
        self.local_config = config['local']

        self.savedir = self.local_config.get('savedir', '.')

    def upload(self, img_capture):
        """
        Copies the files to the local filesystem.
        If the subdirectories don't exist, they will be created.

        :param img_capture: ``ImageCapture`` object
        :return: ImageCapture object
        """

        log.info('Uploading to file system {}'.format(img_capture.clean_fname))

        if not exists(self.savedir):
            raise EnvironmentError('savedir {} does not exist'.format(self.savedir))

        savedir = self.savedir + '/' + img_capture.subdir

        if not exists(savedir):
            makedirs(savedir)

        log.debug('Saving files to {}'.format(savedir))

        box_name = img_capture.full_fname
        nobox_name = img_capture.clean_fname

        box_path = '{}/box/{}'.format(savedir, basename(box_name))
        nobox_path = '{}/nobox/{}'.format(savedir, basename(nobox_name))

        log.debug('Copying {}'.format(box_name))
        copyfile('{}'.format(box_name), box_path)

        log.debug('Copying {}'.format(nobox_name))
        copyfile('{}'.format(nobox_name), nobox_path)

        log.info('File system upload complete {}'.format(img_capture.clean_fname))

        return img_capture
