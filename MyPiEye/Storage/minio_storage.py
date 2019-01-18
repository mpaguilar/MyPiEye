from dateutil import tz

import logging

from minio import Minio

log = logging.getLogger(__name__)


class MinioStorage(object):

    def __init__(self, config):
        self.config = config

        self.minio_config = config['s3_archive']

        # get settings
        self.access_key = self.minio_config.get('access_key', None)
        self.secret_key = self.minio_config.get('secret_key', None)

        self.local_tz = self.config.get('timezone', 'UTC')
        self.local_tz = tz.gettz(self.local_tz)

        # minio settings
        self.bucket_name = self.minio_config.get('bucket_name', None)
        self.region = self.minio_config.get('aws_region')

        self.url = self.minio_config.get('url', None)
        self.mclient = None

    def connect(self):
        self.mclient = Minio(
            self.url,
            access_key=self.access_key,
            secret_key=self.secret_key
        )

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
