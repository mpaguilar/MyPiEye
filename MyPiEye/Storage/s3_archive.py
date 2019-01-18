from datetime import datetime
from os.path import basename
from os import remove

import logging

from .s3_storage import S3Storage as S3Storage
from .minio_storage import MinioStorage as MinioStorage

log = logging.getLogger(__name__)


class S3Archive(object):

    def __init__(self, config):
        self.config = config.get('s3_archive', {})
        self.s3 = S3Storage(config)
        self.mc = MinioStorage(config)

        self.backup_dir = self.config.get('backup_dir', 'files')
        self.remove_remote = self.config.get('remove_remote', True)
        self.remove_local = self.config.get('remove_local', True)

        datestr = datetime.utcnow().strftime('%y%m%d')
        self.date_prefix = '{}/{}'.format(config['s3']['prefix'], datestr)

        self.s3.connect()
        self.mc.connect()

    def archive_file_list(self):
        s3files = self.s3.list_cam_images()

        # get yesterday and anything before that.
        older_files = [x['Key'] for x in s3files if not x['Key'].startswith(self.date_prefix)]

        ret = []

        for of in older_files:
            of_parts = of.split('/')
            cam_id = '/'.join(of_parts[0:2])
            dtpath = of_parts[2]

            item = {
                'remote': of,
                'filename': basename(of),
                'cam_id': cam_id,
                'dtpath': dtpath
            }

            ret.append(item)

        return ret

    def start(self):

        older_files = self.archive_file_list()

        log.info('Preparing to download {} files'.format(len(older_files)))
        log.info('Downloading to {}'.format(self.backup_dir))

        for f in older_files:
            log.info('downloading {}'.format(f['remote']))

            self.s3.download_image(f['remote'])

            obj = '{}/{}/{}'.format(
                f['cam_id'],
                f['dtpath'],
                f['filename']
            )

            log.info('uploading {}'.format(f['filename']))
            self.mc.upload(obj, '{}/{}'.format(self.backup_dir, f['filename']))

            if self.remove_local:
                log.debug('removing local file {}'.format(f['filename']))
                remove('{}/{}'.format(self.backup_dir, f['filename']))

            if self.remove_remote:
                log.debug('removing remote file {}'.format(f['remote']))
                self.s3.delete_image(f['remote'])

        log.info('Archive complete')
        return True
