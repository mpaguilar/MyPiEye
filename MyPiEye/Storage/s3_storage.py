from os.path import basename, dirname
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

        # shortcut
        self.s3_config = config['s3']

        # get settings
        self.aws_access_key_id = self.s3_config['aws_access_key_id']
        self.aws_secret_access_key = self.s3_config['aws_secret_access_key']

        self.local_tz = self.config.get('timezone', 'UTC')
        self.local_tz = tz.gettz(self.local_tz)

        # s3 settings
        self.bucket_name = self.s3_config['bucket_name']
        self.region = self.s3_config['aws_region']

        # if this camera has a different prefix, use it
        self.prefix = self.s3_config.get('prefix', None)
        if self.prefix is None:
            camera_id = self.config['camera']['camera_id']
            log.info('prefix is not found. Using camera_id {}'.format(camera_id))
            self.prefix = camera_id

        # dynamodb settings
        self.camera_table = self.s3_config.get('camera_table', None)
        self.image_table = self.s3_config.get('image_table', None)

        # setup resources

        # uses the access keys one time
        # also, theoretically safer in multithreaded environments,
        # but that's not being used right now.
        self.session = boto3.session.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key)

        # S3
        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.bucket_name)

        # DynamoDb
        db = self.session.resource('dynamodb', region_name=self.region)
        self.camera_table = db.Table(self.camera_table)
        self.image_table = db.Table(self.image_table)

    def update_db(self, upload_path, capture_dt):
        log.info('Updating db for {}'.format(upload_path))

        self.camera_table.put_item(
            Item={
                'cam_id': self.prefix,
                'last_update_utc': datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S'),
                'last_update': datetime.now(self.local_tz).strftime('%Y/%m/%d %H:%M:%S'),
                'filename': upload_path
            }
        )

        self.image_table.put_item(
            Item={
                's3key': upload_path,
                'path': dirname(upload_path),
                'bucket': self.bucket_name,
                'capture_time': capture_dt.strftime('%Y/%m/%d %H:%M:%S')
            }
        )

        log.info('Db updated for {}'.format(upload_path))

    def upload(self, img_capture):

        subdir = img_capture.subdir
        box_name = img_capture.full_fname
        capture_dt = img_capture.capture_dt

        log.info('Uploading {} to S3 prefix {}'.format(box_name, self.prefix))
        bname = basename(box_name)

        upload_path = '{}/{}'.format(subdir, bname)
        if self.prefix != '':
            upload_path = '{}/{}/{}'.format(self.prefix, subdir, bname)

        self.bucket.upload_file(Filename=box_name, Key=upload_path, ExtraArgs={'ContentType': 'image/jpeg'})

        log.info('Upload to S3 complete: {}'.format(upload_path))

        if self.camera_table is not None and self.image_table is not None:
            self.update_db(upload_path, capture_dt)

        log.info('Upload complete {}'.format(box_name))
        return True

    def check(self):
        s3_config = self.config.get('s3', None)
        if s3_config is None:
            log.info('No [s3] section found')
            return True

        ret = True

        if s3_config.get('aws_access_key_id', None) is None:
            log.error('S3: aws_access_key_id is required')
            ret = False

        if s3_config.get('aws_secret_access_key', None) is None:
            log.error('S3: aws_secret_access_key is required')
            ret = False

        if s3_config.get('bucket_name', None) is None:
            log.error('S3: bucket_name is required')
            ret = False

        if s3_config.get('aws_region', None) is None:
            log.error('S3: aws_region is required')
            ret = False

        if s3_config.get('prefix', None) is None:
            log.warning('S3: prefix is empty or missing')

        if s3_config.get('camera_table', None) is None:
            log.warning('AWS: camera_table is empty or missing')

        if s3_config.get('image_table', None) is None:
            log.warning('AWS: image_table is empty or missing')

        return ret

    def configure(self):

        log.warning('All AWS configuration is manual')
        return True
