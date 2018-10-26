import logging
from os.path import exists, join, abspath
from os import makedirs
from dateutil import tz
from datetime import datetime

from MyPiEye.Storage.google_drive import GDriveAuth, GDriveStorage
from MyPiEye.Storage.local_filesystem import FileStorage
from MyPiEye.Storage.s3_storage import S3Storage
from MyPiEye.Storage.google_drive import GDriveStorage, GDriveAuth

log = logging.getLogger(__name__)


class ConfigureApp(object):

    def __init__(self, config):
        self.config = config

    def initialize(self):
        """
        Runs through config settings, creating resources if necessary
        :return: True on success, False on error
        """

        print('initializing')

        success = True

        success = (success and self.prepare_camera())
        success = (success and self.prepare_working_directories())
        success = (success and self.prepare_local_storage())
        success = (success and self.prepare_gdrive())

        return success

    def prepare_camera(self):
        """
        Checks to see if settings exist. Does not use camera.
        :return: True on success
        """

        log.info('Checking camera settings')

        camera = self.config.get('camera', None)
        if camera is None:
            log.error('Camera is required')
            return False

        # click forces a choice, but check it anyway
        res = self.config.get('resolution', None)
        if res is None:
            log.error('resolution must be set')
            return False

        if res != 'small' and res != '720p' and res != '1080p':
            log.error('Invalid resolution: {}'.format(res))
            return False

        return True

    def prepare_working_directories(self):
        """
        Creates `workdir`, for staging file uploads. Must be set.
        :return: True on success.
        """

        log.info('Preparing working directories')
        # create workdir
        if self.config.get('workdir', None) is None:
            log.error('workdir must be set')
            return False

        workdir = self.config['workdir']
        workdir = abspath(workdir)

        if not exists(workdir):
            log.warning('Working directory does not exist: {}. Creating.'.format(workdir))
            makedirs(workdir)

        return True

    def prepare_gdrive(self, credential_filename='google_auth.json'):
        """
         Checks `gdrive` setting, and if set to anything, will attempt to create `credential_folder`.

         Creates `gdrive` folder at root of user's Google Drive. If `google_auth.json` is not found in
         the `credential_folder`, then the user will prompted with a URL and a challenge to code to authorize
         the application with Google.

         This app must create the folder in order to find and use it. The scope is limited to prevent access to
         other files and folders on the user's drive. By default, it won't be able to find anything.

        :param credential_filename: Used for testing.
        :return: True on success.
        """

        log.info('Preparing Google Drive')
        ok = True

        gconfig = self.config.get('gdrive', None)
        if gconfig is None:
            log.info('gdrive section not found. Skipping.')
            return True

        if self.config.get('credential_folder') is None:
            log.error('credential_folder must be set.')
            ok = False

        folder_name = gconfig.get('folder_name', None)
        if folder_name is None:
            log.error('folder_name must be set')
            ok = False

        client_id = None
        client_secret = None
        creds_file = None

        if ok:
            creds_folder = abspath(self.config['credential_folder'])
            creds_file = abspath(join(creds_folder, credential_filename))

            client_id = gconfig.get('client_id', None)
            if client_id is None:
                log.error('GDrive requires client_id')
                ok = False

            client_secret = gconfig.get('client_secret', None)
            if client_secret is None:
                log.error('GDrive requires client_secret')
                ok = False

        if ok:

            log.info('Attempting authentication to GDrive')
            gauth = GDriveAuth.init_gauth(client_id, gconfig['client_secret'], creds_file)

            log.info('Searching for main folder {} on GDrive'.format(folder_name))

            gstorage = GDriveStorage(gauth, folder_name)

            if gstorage.main_folder(create=True) is None:
                log.error('Failed to create google folder.')
                ok = False

        return ok

    def check(self):
        """
        Run through the various settings, and make sure it's good to start
        :return: True if okay, False if not
        """

        ret = True

        # Check all of the settings, report all failures

        # check workdir
        workdir = self.config['workdir']
        if workdir is None:
            log.error('workdir must be set')
            ret = False

        if workdir is not None and not exists(workdir):
            log.error('Working directory does not exist: {}'.format(workdir))
            ret = False

        camera = self.config.get('camera', None)
        if camera is None:
            log.error('camera is required')
            ret = False

        camera_id = self.config.get('camera_id', None)
        if camera_id is None:
            log.error('camera_id is required')
            ret = False

        timezone = self.config.get('timezone', None)
        if tz is None:
            log.warning('timezone is not set')
        else:
            tzstr = tz.gettz(timezone)
            log.info('Timezone set to {}'.format(tzstr))
            now = datetime.now(tzstr).strftime('%Y/%m/%d %H:%M:%S')
            log.info('Local time: {}'.format(now))

        # click forces a choice, but check it anyway
        res = self.config['resolution']

        if res != 'small' and res != '720p' and res != '1080p':
            log.error('Invalid resolution: {}'.format(res))
            ret = False

        if not self.check_filestorage():
            ret = False

        if not self.check_gdrive():
            ret = False

        if not self.check_s3():
            ret = False

        return ret

    def check_filestorage(self):
        localconfig = self.config.get('local', None)
        if localconfig is None:
            log.info('No [local] section found. Skipping.')
            return True

        fs = FileStorage(self.config)
        if not fs.check():
            log.error('Local filesystem check failed')
            return False

        return True

    def check_s3(self):

        s3_config = self.config.get('s3', None)
        if s3_config is None:
            log.info('No [s3] section found')
            return True

        s3 = S3Storage(self.config)
        if not s3.check():
            log.error('AWS check failed')
            return False

        return True

    def check_gdrive(self):

        gconfig = self.config.get('gdrive', None)

        if gconfig is None:
            log.info('No [gdrive] section found')
            return True

        ret = True

        gauth = GDriveAuth(self.config)
        if not gauth.check():
            log.error('GDriveAuth check failed')
            ret = False

        if ret:
            gdrive = GDriveStorage(gauth, self.config)
            if not gdrive.check():
                ret = False
        else:
            log.warning('Failed authorization, skipping GDrive storage check.')

        return ret
