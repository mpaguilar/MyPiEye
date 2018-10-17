from concurrent.futures import ProcessPoolExecutor
import asyncio

from .google_drive import GDriveAuth, GDriveStorage
from .local import local_save


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
            local_fut = loop.run_in_executor(None, local_save, self.fs_path, box_name, nobox_name, subdir)
            futures.append(local_fut)

        if google_drive is not None:
            pass

        gathered = asyncio.gather(*futures)

        loop.run_until_complete(gathered)
