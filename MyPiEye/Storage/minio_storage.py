from datetime import datetime, timedelta
from os import environ
import logging
from io import BytesIO

from minio import Minio

log = logging.getLogger(__name__)


class MinioStorage(object):

    def __init__(self, global_config):

        self.stats = {
            'images_sent': 0,
            'start_time': datetime.now()
        }

        self.global_config = global_config

        self.self_config = global_config['minio']

        self.access_key = self._get_config_value('access_key', 'MINIO_ACCESS_KEY')
        self.secret_key = self.secret_key = self._get_config_value('secret_key', 'MINIO_SECRET_KEY')
        self.bucket_name = self.bucket_name = self._get_config_value('bucket_name', 'MINIO_BUCKET')
        self.url = self._get_config_value('url', 'MINIO_URL')
        self.filename_format = self._get_config_value('filename_format', 'MINIO_FMT')

        if self.filename_format is None:
            self.filename_format = '%Y%m%d/%H%M%S.%f'

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

    def upload(self, jpg, dt_stamp, camera_id):

        bio = BytesIO(jpg)
        filename = '{}/{}.jpg'.format(camera_id, dt_stamp.strftime(self.filename_format))
        dtstr = dt_stamp.isoformat()

        log.info('Uploading to minio {}'.format(filename))
        print('uploading to minio')

        self.mclient.put_object(
            self.bucket_name,
            filename,
            bio,
            len(jpg),
            content_type='image/jpg',
            metadata={
                'timestamp': dtstr,
                'camera_id': camera_id
            }
        )

        log.info('Upload complete {}'.format(filename))
        self.stats['images_sent'] = self.stats['images_sent'] + 1
        ts = datetime.now() - self.stats['start_time']
        print('\nminio {} upload complete in {}\n'.format(self.stats['images_sent'], str(ts)))
        return True
