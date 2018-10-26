import logging
from os.path import exists, join, abspath
from os import makedirs
from dateutil import tz
from datetime import datetime

from MyPiEye.Storage.google_drive import GDriveAuth, GDriveStorage
from MyPiEye.Storage.local_filesystem import FileStorage
from MyPiEye.Storage.s3_storage import S3Storage
from MyPiEye.Storage.google_drive import GDriveStorage, GDriveAuth
from MyPiEye.usbcamera import UsbCamera

log = logging.getLogger(__name__)


class ConfigureApp(object):

    def __init__(self, config):
        self.config = config

    def configure(self):
        ret = True

        if not self.configure_working_directories():
            log.critical('Failed to configure working directories')
            ret = False

        if not self.configure_gdrive():
            log.critical('Failed to configure GDriveStorage')
            ret = False

        return ret

    def configure_working_directories(self):
        """
        Creates ``workdir``, for staging file uploads. Must be set.
        :return: True on success.
        """

        log.info('Preparing working directories')

        workdir = self.config.get('workdir', None)
        if workdir is None:
            log.error('workdir must be set.')
            return False

        workdir = abspath(workdir)

        if not exists(workdir):
            log.warning('Working directory does not exist: {}. Creating.'.format(workdir))
            makedirs(workdir)

        return True

    def configure_gdrive(self):
        gconfig = self.config.get('gdrive', None)

        if gconfig is None:
            log.info('No [gdrive] section found')
            return True

        ret = True

        gauth = GDriveAuth(self.config)
        if not gauth.configure():
            log.error('GDriveAuth check failed')
            ret = False

        if ret:
            gdrive = GDriveStorage(gauth, self.config)
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

        if not self.check_filestorage():
            ret = False

        if not self.check_gdrive():
            ret = False

        if not self.check_s3():
            ret = False

        return ret

    def check_camera(self):

        log.info('Checking camera config')
        config = self.config.get('camera', None)
        if config is None:
            log.error('[camera] section is required')
            return False

        cam = UsbCamera(self.config)

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
        workdir = self.config.get('workdir', None)

        if workdir is None:
            log.error('workdir must be set')
            ret = False
        else:
            if not exists(workdir):
                log.error('Working directory does not exist: {}'.format(workdir))
                ret = False

        timezone = self.config.get('timezone', None)
        if tz is None:
            log.warning('timezone is not set')
        else:
            tzstr = tz.gettz(timezone)
            log.info('Timezone set to {}'.format(tzstr))
            now = datetime.now(tzstr).strftime('%Y/%m/%d %H:%M:%S')
            log.info('Local time: {}'.format(now))

        if not ret:
            log.critical('Global checks failed')
        else:
            log.info('Global checks passed')

        return ret

    def check_filestorage(self):

        log.info('Checking FileStorage')

        localconfig = self.config.get('local', None)
        if localconfig is None:
            log.info('No [local] section found. Skipping.')
            return True

        fs = FileStorage(self.config)
        if not fs.check():
            log.critical('Local filesystem check failed')
            return False

        log.info('Local filesystem checks passed')
        return True

    def check_s3(self):

        log.info('Checking AWS config')

        s3_config = self.config.get('s3', None)
        if s3_config is None:
            log.info('No [s3] section found')
            return True

        s3 = S3Storage(self.config)
        if not s3.check():
            log.critical('AWS check failed')
            return False

        log.info('AWS config checks passed')
        return True

    def check_gdrive(self):

        log.info('Checking GDrive')

        gconfig = self.config.get('gdrive', None)

        if gconfig is None:
            log.info('No [gdrive] section found')
            return True

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
