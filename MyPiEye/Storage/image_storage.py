from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import asyncio

import multiprocessing

from os.path import join, abspath
from os import remove

from .google_drive import GDriveAuth, GDriveStorage
from .local_filesystem import local_save

log = multiprocessing.get_logger()


class ImageStorage(object):

    def __init__(self, fs_path=None, gdrive_settings=None, creds_folder='.'):
        """

        :param fs_path: the local filesystem path
        :param gdrive_settings: the ``[gdrive]`` settings from the .ini file
        """

        pth = abspath(creds_folder)
        self.creds_folder = pth

        self.fs_path = fs_path
        self.gdrive_settings = gdrive_settings

        self.executor = ProcessPoolExecutor(max_workers=2)

        log.debug('ImageStorage initialized')

    @staticmethod
    def do_gdrive(subdir, box_name, folder_name, creds_file, client_id, client_secret):

        log.info('Saving to Google Drive {}'.format(folder_name))
        gauth = GDriveAuth.init_gauth(client_id, client_secret, creds_file)
        gstorage = GDriveStorage(gauth, folder_name)
        gstorage.upload_file(subdir, box_name)

    def save_files(self, subdir, box_name, nobox_name):

        log.info('Saving files in {}'.format(subdir))

        futures = []

        if self.fs_path is not None:
            log.info('Saving to local filesystem {}'.format(self.fs_path))
            # local_save(self.fs_path, box_name, nobox_name, subdir)
            fut = self.executor.submit(local_save, self.fs_path, box_name, nobox_name, subdir)
            futures.append(fut)

        if self.gdrive_settings is not None:
            creds_file = abspath(join(self.creds_folder, 'google_auth.json'))
            folder_name = self.gdrive_settings['folder_name']
            client_id = self.gdrive_settings['client_id']
            client_secret = self.gdrive_settings['client_secret']

            fut = self.executor.submit(ImageStorage.do_gdrive,
                                       subdir, box_name, folder_name,
                                       creds_file, client_id, client_secret)
            futures.append(fut)

        _, waiting = wait(futures)

        log.debug('Removing {}'.format(box_name))
        remove(box_name)
        log.debug('Removing {}'.format(nobox_name))
        remove(nobox_name)
