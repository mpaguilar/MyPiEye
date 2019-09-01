from dateutil import tz
from os import environ
import logging

from minio import Minio

log = logging.getLogger(__name__)


class MinioStorage(object):

    def __init__(self, global_config):
        self.global_config = global_config

        self.self_config = global_config['minio']

        self.access_key = self._get_config_value('access_key', 'MINIO_ACCESS_KEY')
        self.secret_key = self.secret_key = self._get_config_value('secret_key', 'MINIO_SECRET_KEY')
        self.bucket_name = self.bucket_name = self._get_config_value('bucket_name')
        self.url = self._get_config_value('url')

        self.mclient = Minio(
            self.url,
            access_key=self.access_key,
            secret_key=self.secret_key
        )

    def _get_config_value(self, key_name, env_name):
        """
        If the environment variable is found, the config
        object will be updated with it's value
        :param key_name:
        :param env_name:
        :return:
        """
        val = environ.get(env_name)
        if val is None:
            val = self.self_config.get(key_name, None)
        else:
            self.self_config[key_name] = val

        return val

    def check(self):
        ret = True

        if self.access_key is None:
            log.error('No minio access key found')
            ret = False

        if self.secret_key is None:
            log.error('No minio secret key found')
            ret = False

        if self.bucket_name is None:
            log.error('No bucket name found')
            ret = False

        if self.url is None:
            log.error('No url found')
            ret = False

        return ret

    def configure(self):

        exists = self.mclient.bucket_exists(self.bucket_name)
        if not exists:
            self.mclient.make_bucket(self.bucket_name)

        return True

    def upload(self, object_name, filename):

        if self.mclient is None and not self.connect():
            raise Exception('Not connected')

        log.info('Uploading {} to S3 prefix {}'.format(filename, object_name))
        self.mclient.fput_object(self.bucket_name, object_name, filename)
        log.info('Upload complete {}'.format(filename))
        return True
