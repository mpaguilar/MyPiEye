from shutil import copyfile
from os.path import dirname, basename, exists
from os import remove, makedirs
from googleapiclient.errors import HttpError

from multiprocessing import Process

from time import sleep

import logging

from .google_drive import GDrive

SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'MyPiEye Motion Detection'

log = logging.getLogger(__name__)


class FileUpload(Process):
    """
    Called for multiprocessing.
    """
    def __init__(self, file_queue, savedir=None, gdrive_folder=None):

        Process.__init__(self)
        self.file_queue = file_queue

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

    # per-instance initialization needs to occur here
    def run(self):
        if self.gdrive_folder:
            self.init_google()

        while True:
            next_file = self.file_queue.get()
            log.debug('Received file to upload')

            if next_file is None:
                self.file_queue.task_done()
                log.warning("Stopping upload queue")
                break
            box_name, nobox_name, folder = next_file

            self.upload_file(box_name, nobox_name, folder)

            self.file_queue.task_done()
            sleep(.2)

    def init_google(self):
        self.gdrive = GDrive(SCOPES, APPLICATION_NAME,
                             'creds/motion_detect_app.json', 'creds/motion_detect_user.json')

    def copy_file(self, box_name, nobox_name, folder):
        """

        :param box_name:
        :param nobox_name:
        :param folder:
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

        save_folder = self.gdrive_folder + '/{}'.format(folder)
        log.debug("Uploading {} to google/{}".format(box_name, save_folder))

        try:
            self.gdrive.put_image(box_name, save_folder)
        except TimeoutError:
            log.error('Upload timed out')
        except HttpError:
            log.error('500 error uploading')
        except Exception as e:
            log.critical('Unexpected! {}'.format(e))
            raise e

    def upload_file(self, box_name, nobox_name, folder):

        if self.savedir:
            self.copy_file(box_name, nobox_name, folder)

        if self.gdrive:
            self.google_upload(box_name, folder)

        remove(box_name)
        remove(nobox_name)
