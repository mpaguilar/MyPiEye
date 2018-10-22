from concurrent.futures import ProcessPoolExecutor
import asyncio
import logging
from os.path import join, abspath
from os import remove

import requests.exceptions

from .google_drive import GDriveAuth, GDriveStorage
from .local_filesystem import local_save

log = logging.getLogger(__name__)


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

    def save_files(self, subdir, box_name, nobox_name):

        loop = asyncio.get_event_loop()

        futures = []

        if self.fs_path is not None:
            log.info('Saving to local filesystem {}'.format(self.fs_path))
            local_fut = loop.run_in_executor(None, local_save, self.fs_path, box_name, nobox_name, subdir)
            futures.append(local_fut)

        if self.gdrive_settings is not None:
            creds_file = abspath(join(self.creds_folder, 'google_auth.json'))

            folder_name = self.gdrive_settings['folder_name']
            client_id = self.gdrive_settings['client_id']
            client_secret = self.gdrive_settings['client_secret']

            log.info('Saving to Google Drive {}'.format(folder_name))
            gauth = GDriveAuth.init_gauth(client_id, client_secret, creds_file)
            gstorage = GDriveStorage(gauth, folder_name)
            gdrive_fut = loop.run_in_executor(None, gstorage.upload_file, subdir, box_name)
            futures.append(gdrive_fut)

        gathered = asyncio.gather(*futures)

        try:
            loop.run_until_complete(gathered)
        except requests.exceptions.HTTPError as http_err:
            log.critical('Error: {}'.format(http_err))

        log.info('Files saved')
        log.debug('Removing {}'.format(box_name))
        remove(box_name)
        log.debug('Removing {}'.format(nobox_name))
        remove(nobox_name)
