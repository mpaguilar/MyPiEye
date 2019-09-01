import os
import datetime

import cv2
from azure.storage.blob import BlockBlobService, PublicAccess, ContentSettings

import multiprocessing

log = multiprocessing.log_to_stderr()


class AzureBlobStorage(object):

    def __init__(self, global_config):
        self.global_config = global_config

        self.self_config = global_config['azure_blob']
        self.account = self._config('account', 'AZBLOB_ACCOUNT')
        self.key = self._config('key', 'AZBLOB_KEY')
        self.container = self._config('container', 'AZBLOB_CONTAINER')

        self.blob_service: BlockBlobService = BlockBlobService(self.account, self.key)
        # self.imgobj = imgobj

    def _config(self, key_name, env_name):
        """
        If the environment variable is found, the config
        object will be updated with it's value
        :param key_name:
        :param env_name:
        :return:
        """
        val = os.environ.get(env_name)
        if val is None:
            val = self.self_config.get(key_name, None)
        else:
            self.self_config[key_name] = val

        return val

    def configure(self):
        containers = self.blob_service.list_containers()

        names = [item.name for item in containers.items]

        if self.container not in names:
            self.blob_service.create_container(self.container)

        return True

    def check(self):
        ret = True

        if self.account is None:
            log.error('Azure storage_account not set')
            ret = False

        if self.key is None:
            log.error('Azure storage_key not set')
            ret = False

        if self.container is None:
            log.error('Azure container is not set')
            ret = False

        return ret

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
