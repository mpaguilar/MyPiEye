from concurrent.futures import ProcessPoolExecutor
import asyncio
import logging

from .google_drive import GDriveAuth, GDriveStorage
from .local import local_save

CLIENT_ID = '990858881415-u53d5skorvuuq4hqjfj5pvq80d059744.apps.googleusercontent.com'
CLIENT_SECRET = '-9q0wn7j8x7IGrCRcwuzQY0g'

log = logging.getLogger(__name__)


class ImageStorage(object):

    def __init__(self, fs_path=None, gdrive_folder=None):
        """

        :param fs_path: the local filesystem path
        :param gdrive_folder: the folder name on Google Drive
        """
        self.fs_path = fs_path
        self.gdrive_folder = gdrive_folder
        self.executor = ProcessPoolExecutor(max_workers=2)

    def save_files(self, subdir, box_name, nobox_name):

        loop = asyncio.get_event_loop()

        futures = []

        if self.fs_path is not None:
            log.info('Saving to local filesystem {}'.format(self.fs_path))
            local_fut = loop.run_in_executor(None, local_save, self.fs_path, box_name, nobox_name, subdir)
            futures.append(local_fut)

        if self.gdrive_folder is not None:
            log.info('Saving to Google Drive {}'.format(self.gdrive_folder))
            gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
            gstorage = GDriveStorage(gauth, 'mypieye_test')
            gdrive_fut = loop.run_in_executor(None, gstorage.upload_file, subdir, box_name)
            futures.append(gdrive_fut)

        gathered = asyncio.gather(*futures)

        loop.run_until_complete(gathered)
