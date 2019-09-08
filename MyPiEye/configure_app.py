import logging
from os.path import exists, join, abspath
from os import makedirs
from dateutil import tz
from datetime import datetime

from MyPiEye.Storage.local_storage import LocalStorage
from MyPiEye.Storage.s3_storage import S3Storage
from MyPiEye.Storage.google_drive import GDriveStorage, GDriveAuth
from MyPiEye.usbcamera import UsbCamera
from MyPiEye.Storage.azure_blob import AzureBlobStorage
from MyPiEye.Storage.minio_storage import MinioStorage
from MyPiEye.Storage.redis_storage import RedisStorage
from MyPiEye.Storage.celery_storage import CeleryStorage

from MyPiEye.CLI import get_config_value, get_self_config_value

log = logging.getLogger(__name__)


class ConfigureApp(object):

    def __init__(self, config, **kwargs):
        self.self_config = config
        self.args = kwargs

    def configure(self):
        ret = True

        if not self.configure_working_directories():
            ret = False

        if not self.configure_local_filesystem():
            ret = False

        if not self.configure_minio():
            ret = False

        if not self.configure_azure_blob():
            ret = False

        if not self.configure_redis():
            ret = False

        if not self.configure_celery():
            ret = False

        return ret

    def is_enabled(self, key_name, env_name):
        return get_config_value(
            self.self_config, 'multi', key_name, env_name, False) \
               in [True, 'True']

    def configure_working_directories(self):
        """
        Creates ``workdir``, for staging file uploads. Must be set.
        :return: True on success.
        """

        log.info('Preparing working directories')

        workdir = get_self_config_value(self, 'workdir', 'WORKDIR')
        if workdir is None:
            log.error('workdir must be set.')
            return False

        workdir = abspath(workdir)

        if not exists(workdir):
            log.warning('Working directory does not exist: {}. Creating.'.format(workdir))
            makedirs(workdir)

        return True

    def configure_local_filesystem(self):
        log.info('Configuring local filesystem')

        if not self.is_enabled('enable_local', 'MULTI_LOCAL'):
            log.info('Local saving disabled. Skipping.')
            return True

        # is there a [local] section?
        local_config = self.self_config.get('local', None)
        if local_config is None:
            log.info('[local] section not found. Skipping.')
            return False

        fs = LocalStorage(self.self_config)

        ret = fs.configure()
        if ret:
            log.info('Local filesystem storage configuration complete')
        else:
            log.error('Local filesystem storage configuration failed')

        return ret

    def configure_azure_blob(self):

        if not self.is_enabled('enable_azblob', 'MULTI_AZBLOB'):
            log.info('Azure Blob disabled. Skipping.')
            return True

        ret = True

        log.info('Configuring Azure Blob')
        azblob = AzureBlobStorage(self.config)
        if not azblob.configure():
            log.error('Azure Blob configuration failed')
            ret = False

        return ret

    def configure_minio(self):
        ret = True

        if not self.is_enabled('enable_minio', 'MULTI_MINIO'):
            log.info('minio disabled. Skipping.')
            return True

        log.info('Configuring minio')

        mio = MinioStorage(self.self_config)
        if not mio.configure():
            log.error('minio configuration failed')
            ret = False

        return ret

    def configure_celery(self):
        ret = True

        if not self.is_enabled('enable_celery', 'MULTI_CELERY'):
            log.info('Celery disabled. Skipping.')
            return True

        log.info('Configuring Celery')

        cel = CeleryStorage(self.self_config)
        if not cel.configure():
            log.error('Celery configuration failed')
            ret = False

        return ret

    def configure_redis(self):
        ret = True

        if not self.is_enabled('enable_redis', 'MULTI_REDIS'):
            log.info('redis disabled. Skipping.')
            return True

        log.info('Configuring redis')

        rds = RedisStorage(self.self_config)
        if not rds.configure():
            log.error('redis configuration failed')
            ret = False

        return ret

    def configure_aws(self):
        log.info('Configuring AWS')

        if not self.is_enabled('enable_s3', 'MULTI_S3'):
            log.info('S3 disabled. Skipping')
            return True

        aws = S3Storage(self.self_config)
        chk = aws.configure()

        if chk:
            log.info('AWS config complete')
        else:
            log.critical('AWS config failed')

        return chk

    def configure_gdrive(self):

        log.warning('This component is a mess')

        if not self.is_enabled('enable_gdrive', 'MULTI_GDRIVE'):
            log.info('GDrive disabled. Skipping')
            return True

        gconfig = self.self_config.get('gdrive', None)
        if gconfig is None:
            log.info('No [gdrive] section found')
            return False

        ret = True

        gauth = GDriveAuth(self.self_config)
        if not gauth.configure():
            log.error('GDriveAuth check failed')
            ret = False

        if ret:
            gdrive = GDriveStorage(gauth, self.self_config)
            if not gdrive.configure():
                log.error('Failed to configure GDrive')
                ret = False
        else:
            log.error('Failed authorization, skipping GDrive storage check.')

        return ret

    ## Checks

    def check(self):
        """
        Run through the various settings, and make sure it's good to start
        :return: True if okay, False if not
        """

        ret = True

        # Check all of the settings, report all failures

        if not self.check_global():
            ret = False

        if not self.check_camera():
            ret = False

        if not self.check_localstorage():
            ret = False

        if not self.check_gdrive():
            ret = False

        if not self.check_s3():
            ret = False

        if not self.check_azblob():
            ret = False

        if not self.check_minio():
            ret = False

        if not self.check_celery():
            ret = False

        return ret

    def check_camera(self):

        log.info('Checking camera config')

        if not self.is_enabled('enable_camera', 'MULTI_CAMERA'):
            log.info('Camera disabled. Skipping.')
            return True

        config = self.self_config.get('camera', None)
        if config is None:
            log.error('[camera] section is required')
            return False

        cam = UsbCamera(self.self_config)

        chk = cam.check()

        if not chk:
            log.critical('Camera config checks failed')
        else:
            log.info('Camera config checks passed')

        return chk

    def check_global(self):
        ret = True

        log.info('Checking global config')

        # check workdir
        workdir = get_self_config_value(self, 'workdir', 'WORKDIR')

        if workdir is None:
            log.error('workdir must be set')
            ret = False
        else:
            if not exists(workdir):
                log.error('Working directory does not exist: {}'.format(workdir))
                ret = False

        timezone = get_self_config_value(self, 'timezone', 'TIMEZONE', None)
        if tz is None:
            log.warning('timezone is not set')
        else:
            tzstr = tz.gettz(timezone)
            log.info('Timezone set to {}'.format(tzstr))
            now = datetime.now(tzstr).strftime('%Y/%m/%d %H:%M:%S')
            log.info('Local time: {}'.format(now))

        # a [multi] section is required

        multi = self.self_config.get('multi', None)
        if multi is None:
            log.error('No [multi] config section')
            ret = False

        if not ret:
            log.critical('Global checks failed')
        else:
            log.info('Global checks passed')

        return ret

    def check_azblob(self):
        log.info('Checking Azure Blob')

        if not self.is_enabled('enable_azblob', 'MULTI_AZBLOB'):
            log.info('Azure Blob disabled. Skipping.')
            return True

        azconfig = self.self_config.get('azure_blob', None)
        if azconfig is None:
            log.error('No [azure_blob] section found.')
            return False

        azblob = AzureBlobStorage(self.self_config)

        if not azblob.check():
            log.error('Azure Blob checks failed')
            return False

        log.info('Azure Blob okay')

        return True

    def check_minio(self):

        log.info('Checking minio')
        if not self.is_enabled('enable_minio', 'MULTI_MINIO'):
            log.info('minio disabled. Skipping.')
            return True

        mconfig = self.self_config.get('minio', None)
        if mconfig is None:
            log.info('No [minio] section found.')
            return False

        mio = MinioStorage(self.self_config)

        if not mio.check():
            log.error('minio check failed')
            return False

        log.info('minio configuration okay')
        return True

    def check_celery(self):
        log.info('Checking celer')
        if not self.is_enabled('enable_celery', 'MULTI_MINIO'):
            log.info('Celery disabled. Skipping.')
            return True

        rconfig = self.self_config.get('celery')
        if rconfig is None:
            log.error('No [celery] section found.')
            return False

        cel = CeleryStorage(self.self_config)

        if not cel.check():
            log.error('Celery check failed')
            return False

        log.info('Celery configuration okay')
        return True

    def check_redis(self):
        log.info('Checking redis')
        if not self.is_enabled('enable_redis', 'MULTI_MINIO'):
            log.info('redis disabled. Skipping.')
            return True

        rconfig = self.self_config.get('redis')
        if rconfig is None:
            log.error('No [redis] section found.')
            return False

        rds = RedisStorage(self.self_config)

        if not rds.check():
            log.error('redis check failed')
            return False

        log.info('redis configuration okay')
        return True

    def check_localstorage(self):

        log.info('Checking LocalStorage')

        if not self.is_enabled('enable_local', 'MULTI_LOCAL'):
            log.info('Local storage disabled. Skipping.')
            return True

        localconfig = self.self_config.get('local', None)
        if localconfig is None:
            log.info('No [local] section found. Skipping.')
            return False

        fs = LocalStorage(self.self_config)
        if not fs.check():
            log.critical('Local storage check failed')
            return False

        log.info('Local storage checks passed')
        return True

    def check_s3(self):

        log.info('Checking AWS config')

        if not self.is_enabled('enable_s3', 'MULTI_S3'):
            log.info('AWS S3 disabled. Skipping.')
            return True

        s3_config = self.self_config.get('s3', None)
        if s3_config is None:
            log.info('No [s3] section found')
            return False

        s3 = S3Storage(self.self_config)

        if not s3.check():
            log.critical('AWS check failed')
            return False

        log.info('AWS config checks passed')
        return True

    def check_gdrive(self):

        log.info('Checking GDrive')
        if not self.is_enabled('enable_gdrive', 'MULTI_GDRIVE'):
            log.info('GDrive disabled. Skipping.')
            return True

        gconfig = self.config.get('gdrive', None)

        if gconfig is None:
            log.info('No [gdrive] section found')
            return False

        ret = True

        gauth = GDriveAuth(self.config)
        if not gauth.check():
            log.error('GDriveAuth check failed')
            ret = False
        else:
            log.info('GDriveAuth check passed')

        if ret:
            gdrive = GDriveStorage(gauth, self.config)
            if not gdrive.check():
                log.error('GDrive checks failed')
                ret = False
        else:
            log.warning('Failed authorization, skipping GDrive storage check.')

        if ret:
            log.info("GDrive config checks passed")
        else:
            log.critical('GDrive checks failed.')

        return ret
