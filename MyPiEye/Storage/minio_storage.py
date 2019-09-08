from datetime import datetime, timedelta
from os.path import basename
import logging
from io import BytesIO

from minio import Minio
import cv2

from MyPiEye.CLI import get_self_config_value

log = logging.getLogger(__name__)


class MinioStorage(object):

    def __init__(self, global_config):

        self.stats = {
            'images_sent': 0,
            'start_time': datetime.now()
        }

        self.global_config = global_config

        # required for ``get_config_value`` to work
        self.self_config = global_config['minio']

        self.access_key = \
            get_self_config_value(self, 'access_key', 'MINIO_ACCESS_KEY')

        self.secret_key = \
            self.secret_key = get_self_config_value(self, 'secret_key', 'MINIO_SECRET_KEY')

        self.bucket_name = \
            self.bucket_name = get_self_config_value(self, 'bucket_name', 'MINIO_BUCKET')

        self.url = \
            get_self_config_value(self, 'url', 'MINIO_URL')

        self.filename_format = \
            get_self_config_value(self, 'filename_format', 'MINIO_FMT')

        if self.filename_format is None:
            self.filename_format = '%Y%m%d/%H%M%S.%f'

        self.mclient = Minio(
            self.url,
            access_key=self.access_key,
            secret_key=self.secret_key
        )

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

    def upload(self, cv2_imgbuf, dt_stamp, camera_id):

        (ok, jpg) = cv2.imencode('.jpg', cv2_imgbuf)

        if not ok:
            log.error('Error encoding file to jpeg')
            return False

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

    def download_img(self, dt_stamp: datetime, camera_id):

        path = '{}/{}.jpg'.format(camera_id, dt_stamp.strftime(self.filename_format))
        ret = self.mclient.fget_object(self.bucket_name, path, basename(path))
        return ret

    def download_file(self, path):
        ret = self.mclient.fget_object(self.bucket_name, path, basename(path))
        meta = dict(ret.metadata)
        meta.update({'size': ret.size})
        return meta
