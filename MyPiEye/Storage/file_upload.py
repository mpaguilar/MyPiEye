from shutil import copyfile
from os.path import basename, exists
from os import remove, makedirs

import logging

from .google_drive import GDriveAuth

SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'MyPiEye Motion Detection'

log = logging.getLogger(__name__)


class FileUpload(object):
    """
    Manages file uploads. Must be importable for multiprocessing.
    """
    def __init__(self, savedir=None, gdrive_folder=None):

        self.gdrive = None
        self.savedir = None
        self.gdrive_folder = None

        if gdrive_folder:
            self.gdrive_folder = gdrive_folder
            self.init_google()
            log.info('Upload to google folder: {}'.format(gdrive_folder))

        if savedir:
            log.info('Save to directory: {}'.format(savedir))
            self.savedir = savedir

    def init_google(self):
        self.gdrive = GDrive(SCOPES, APPLICATION_NAME,
                             'creds/mypieye_app.json', 'creds/mypieye_user.json')

    def copy_file(self, box_name, nobox_name, folder):
        """

        :param box_name: the filename of the image with boxes
        :param nobox_name: the filename of a clean image
        :param folder: the subfolder to store them in
        :return:
        """

        if not exists(self.savedir):
            raise EnvironmentError('savedir {} does not exist'.format(self.savedir))

        savedir = self.savedir + '/' + folder

        if not exists(savedir):
            makedirs(savedir)

        if not exists(savedir + '/box'):
            makedirs(savedir + '/box')

        if not exists(savedir + '/nobox'):
            makedirs(savedir + '/nobox')

        log.debug('Saving files to {}'.format(savedir))

        copyfile('{}'.format(box_name),
                 '{}/box/{}'.format(savedir, basename(box_name)))

        copyfile('{}'.format(nobox_name),
                 '{}/nobox/{}'.format(savedir, basename(nobox_name)))

    def google_upload(self, box_name, folder):

        pass

    def upload_file(self, box_name, nobox_name, folder):

        if self.savedir:
            self.copy_file(box_name, nobox_name, folder)

        if self.gdrive:
            self.google_upload(box_name, folder)

        remove(box_name)
        remove(nobox_name)
