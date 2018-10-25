from os.path import basename
from datetime import datetime
from dateutil import tz

import multiprocessing

import logging
import boto3
boto3.set_stream_logger('', logging.INFO)

log = multiprocessing.get_logger()


class S3Storage(object):
    def __init__(self, config):
        self.config = config
        self.s3_config = config['s3']

        self.local_tz = self.config.get('timezone', 'UTC')
        self.local_tz = tz.gettz(self.local_tz)

        self.bucket_name = self.s3_config['bucket_name']
        self.prefix = self.s3_config.get('prefix', '')

        self.aws_access_key_id = self.s3_config['aws_access_key_id']
        self.aws_secret_access_key = self.s3_config['aws_secret_access_key']

        self.session = boto3.session.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key)

        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.bucket_name)
        self.region = self.s3_config['aws_region']

        db = self.session.resource('dynamodb', region_name=self.region)
        self.camera_table = db.Table('HouseCams')
        self.image_table = db.Table('ImageData')

    def upload(self, subdir, box_name, capture_dt):
        log.info('Uploading {} to S3 prefix {}'.format(box_name, self.prefix))
        bname = basename(box_name)

        upload_path = '{}/{}'.format(subdir, bname)
        if self.prefix != '':
            upload_path = '{}/{}/{}'.format(self.prefix, subdir, bname)

        self.bucket.upload_file(Filename=box_name, Key=upload_path, ExtraArgs={'ContentType': 'image/jpeg'})

        log.info('Upload to S3 complete: {}'.format(upload_path))
        log.debug('Updating db')

        self.camera_table.put_item(
            Item={
                'cam_id': self.s3_config.get('prefix', 'no_id'),
                'last_update_utc': datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S'),
                'last_update': datetime.now(self.local_tz).strftime('%Y/%m/%d %H:%M:%S'),
                'filename': upload_path
            }
        )

        self.image_table.put_item(
            Item={
                's3key': upload_path,
                'bucket': self.bucket_name,
                'capture_time': capture_dt.strftime('%Y/%m/%d %H:%M:%S')
            }
        )
        log.info('Upload complete {}'.format(box_name))
        return True
