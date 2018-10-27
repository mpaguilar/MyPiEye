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

        self.savedir = self.local_config.get('savedir', None)

    def upload(self, img_capture):
        """
        Copies the files to the local filesystem.
        If the subdirectories don't exist, they will be created.

        :param img_capture: ``ImageCapture`` object
        :return: ImageCapture object
        """

        log.info('Uploading to file system {}'.format(img_capture.clean_fname))

        box_name = img_capture.full_fname
        nobox_name = img_capture.clean_fname

        box_dir = '{}/box/{}'.format(self.savedir, img_capture.subdir)
        if not exists(box_dir):
            log.warning('Creating subdirectory {}'.format(box_dir))
            makedirs(box_dir)

        box_path = '{}/{}'.format(box_dir, basename(box_name))

        nobox_dir = '{}/nobox/{}'.format(self.savedir, img_capture.subdir)
        if not exists(nobox_dir):
            log.warning('Creating subdirectory {}'.format(nobox_dir))
            makedirs(nobox_dir)

        nobox_path = '{}/{}'.format(nobox_dir, basename(nobox_name))

        log.debug('Copying {}'.format(box_path))
        copyfile('{}'.format(box_name), box_path)

        log.debug('Copying {}'.format(nobox_path))
        copyfile('{}'.format(nobox_name), nobox_path)

        log.info('File system upload complete {}'.format(img_capture.clean_fname))

        return img_capture

    def configure(self):
        if not exists(self.savedir):
            log.warning('FS: Creating save directory {}'.format(self.savedir))
            makedirs(self.savedir)

        box_dir = '{}/box'.format(self.savedir)
        if not exists(box_dir):
            log.warning('FS: Creating box save directory: {}'.format(box_dir))
            makedirs(box_dir)

        nobox_dir = '{}/nobox'.format(self.savedir)
        if not exists(nobox_dir):
            log.warning('FS: Creating nobox save directory: {}'.format(nobox_dir))
            makedirs(nobox_dir)

        return True

    def check(self):

        ok = True

        if self.savedir is None:
            log.error('FS: savedir is required')

        if not exists(self.savedir):
            log.error('FS: Save directory does not exist: {}'.format(self.savedir))
            ok = False

        box_dir = '{}/box'.format(self.savedir)
        if not exists(box_dir):
            log.error('FS: box save directory does not exist: {}'.format(box_dir))
            ok = False

        nobox_dir = '{}/nobox'.format(self.savedir)
        if not exists(nobox_dir):
            log.error('FS: nobox save directory does not exist: {}'.format(nobox_dir))
            ok = False

        return ok
