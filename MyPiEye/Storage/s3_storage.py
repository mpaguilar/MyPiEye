from os.path import basename
import multiprocessing

import boto3

log = multiprocessing.get_logger()


class S3Storage(object):
    def __init__(self, config):
        self.s3_config = config['s3']

        self.bucket_name = self.s3_config['bucket_name']
        self.prefix = self.s3_config.get('prefix', '')

        self.aws_access_key_id = self.s3_config['aws_access_key_id']
        self.aws_secret_access_key = self.s3_config['aws_secret_access_key']

        self.session = boto3.session.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key)

        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.bucket_name)

    def upload(self, subdir, box_name):
        log.info('Uploading to S3 {}'.format(box_name))
        bname = basename(box_name)

        upload_path = '{}/{}'.format(subdir, bname)
        if self.prefix != '':
            upload_path = '{}/{}/{}'.format(self.prefix, subdir, bname)

        self.bucket.upload_file(Filename=box_name, Key=upload_path, ExtraArgs={'ContentType': 'image/jpeg'})
        log.info('Upload complete {}'.format(box_name))
        return True
