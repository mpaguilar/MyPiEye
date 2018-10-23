from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import asyncio

import multiprocessing

from os.path import join, abspath
from os import remove

from .google_drive import GDriveAuth, GDriveStorage
from .local_filesystem import local_save

log = multiprocessing.get_logger()


class ImageStorage(object):
    executor = ProcessPoolExecutor(max_workers=4)

    def __init__(self, config, creds_folder='.'):
        """

        :param config: the main config
        :param creds_folder: where to store the .json (unused?)
        """

        pth = abspath(creds_folder)
        self.creds_folder = pth
        self.config = config

        self.fs_path = self.config['savedir']
        self.gdrive_settings = self.config.get('gdrive', None)
        self.futures = []

        log.debug('ImageStorage initialized')

    @staticmethod
    def do_gdrive(subdir, box_name, folder_name, creds_file, client_id, client_secret):

        log.info('Saving to Google Drive {}'.format(folder_name))
        gauth = GDriveAuth.init_gauth(client_id, client_secret, creds_file)
        gstorage = GDriveStorage(gauth, folder_name)
        gstorage.upload_file(subdir, box_name)

    @staticmethod
    def save(config, subdir, box_name, nobox_name):
        futures = []
        fs_path = config.get('savedir', None)
        if fs_path is not None:
            log.info('Saving to local filesystem {}'.format(fs_path))
            # local_save(self.fs_path, box_name, nobox_name, subdir)
            local_save(fs_path, box_name, nobox_name, subdir)

        gdrive_settings = config.get('gdrive', None)
        creds_folder = config.get('credential_folder', '.')

        if gdrive_settings is not None:
            creds_file = abspath(join(creds_folder, 'google_auth.json'))
            folder_name = gdrive_settings['folder_name']
            client_id = gdrive_settings['client_id']
            client_secret = gdrive_settings['client_secret']

            ImageStorage.do_gdrive(subdir, box_name, folder_name,
                                   creds_file, client_id, client_secret)

        log.debug('Removing {}'.format(box_name))
        remove(box_name)
        log.debug('Removing {}'.format(nobox_name))
        remove(nobox_name)

        return True

    def save_files(self, subdir, box_name, nobox_name):

        fut = ImageStorage.executor.submit(ImageStorage.save, self.config, subdir, box_name, nobox_name)
        self.futures.append(fut)
        _, waiting = wait(self.futures, .1)
        self.futures = list(waiting)

        return
