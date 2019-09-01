import os
import datetime

import cv2
from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

import multiprocessing

log = multiprocessing.log_to_stderr()


class AzureBlobStorage(object):

    def __init__(self, config):
        self.config = config

        self.azconfig = config['azure_blob']
        self.account = None
        self.key = None
        self.container = None

        self.blob_service: BlockBlobService = None
        # self.imgobj = imgobj

    def configure(self):

        auth = self.get_auth()
        if auth is None:
            log.error('Failed to initialize auth')
            return False

        self.container = self.azconfig.get('container_name', None)
        if self.container is None:
            log.error('container_name setting is required in [azure_blob] section')
            return False

        self.account, self.key = auth
        self.blob_service = BlockBlobService(self.account, self.key)

        return True

    def get_auth(self):
        """
        Accounts and keys may be handled via .ini or environment variables.
        ```
        AZBLOB_ACCOUNT
        AZBLOB_KEY
        ```
        :return:
        """

        account = os.environ.get('AZBLOB_ACCOUNT', None)
        if account is None:
            account = self.azconfig.get('storage_account', None)

        if account is None:
            log.error('No account for azure blob')
            return None

        key = os.environ.get('AZBLOB_KEY', None)
        if key is None:
            key = self.azconfig.get('storage_key', None)

        if key is None:
            log.error('No key for azure blob')
            return None

        return account, key

    @staticmethod
    def upload_progress(current, total):
        print('uploading pic: ({}, {})'.format(current, total))

    def save(self, jpg, filename, dtstamp: str, camera_id):

        self.blob_service.create_blob_from_bytes(
            self.container,
            filename,
            jpg.tobytes(),
            content_settings=ContentSettings(content_type='image/jpg'),
            metadata={
                'timestamp': dtstamp,
                'camera_id': camera_id
            },
            progress_callback=AzureBlobStorage.upload_progress
        )
