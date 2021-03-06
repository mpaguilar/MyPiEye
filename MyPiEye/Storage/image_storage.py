from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import asyncio

import multiprocessing

from os.path import join, abspath
from os import remove

from .google_drive import GDriveAuth, GDriveStorage
from .s3_storage import S3Storage
from .local_storage import LocalStorage

from MyPiEye.motion_detect import ImageCapture

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
        self.s3_config = self.config.get('s3', None)
        self.futures = []

        # how many items to have queued and processing.
        self.process_limit = multiprocessing.Semaphore(30)
        self._pcount = 0

        log.debug('ImageStorage initialized')

    @staticmethod
    def save(config, img_capture: ImageCapture):
        """
        Entry point for Executor. Deletes the ImageCapture on completion.

        :param config: main config dictionary
        :param img_capture: ``ImageCapture`` object.
        :return:
        """

        localstorage = config.get('local', None)
        if localstorage is not None:
            log.info('Saving to local filesystem {}'.format(img_capture.base_filename))
            # local_save(fs_path, img_capture)
            fs = LocalStorage(config)
            fs.upload(img_capture)

        s3_config = config.get('s3', None)
        if s3_config is not None:
            s3 = S3Storage(config)
            if not s3.upload(img_capture):
                log.error('Error uploading to AWS')

        gdrive_settings = config.get('gdrive', None)
        creds_folder = config.get('credential_folder', '.')

        if gdrive_settings is not None:
            creds_file = abspath(join(creds_folder, 'google_auth.json'))
            folder_name = gdrive_settings['folder_name']
            client_id = gdrive_settings['client_id']
            client_secret = gdrive_settings['client_secret']

            log.info('Saving to Google Drive {}'.format(folder_name))
            gauth = GDriveAuth.init_gauth(client_id, client_secret, creds_file)
            gstorage = GDriveStorage(gauth, folder_name)
            gstorage.upload_file(img_capture)

        del img_capture

        return True

    def save_files(self, img_capture: ImageCapture):
        """
        Launches the processes to save files.

        :param img_capture: ``ImageCapture`` object.
        :return:
        """

        # img_capture.full_image = None
        # img_capture.clean_image = None
        # img_capture.ts_image = None

        lock = self.process_limit.acquire(False)
        if lock:

            self._pcount = self._pcount + 1
            log.info('pcount: {}'.format(self._pcount))

            fut = ImageStorage.executor.submit(ImageStorage.save, self.config, img_capture)
            self.futures.append(fut)
            _, waiting = wait(self.futures, .1)
            self.futures = list(waiting)

            self.process_limit.release()
            self._pcount = self._pcount - 1
            log.info('pcount: {}'.format(self._pcount))
        else:
            log.warning('Too many images queued, skipping {}'.format(img_capture.base_filename))

        return
