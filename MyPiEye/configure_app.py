import logging
from os.path import exists, join, abspath
from os import makedirs

from MyPiEye.Storage.google_drive import GDriveAuth, GDriveStorage

CLIENT_ID = '990858881415-u53d5skorvuuq4hqjfj5pvq80d059744.apps.googleusercontent.com'
CLIENT_SECRET = '-9q0wn7j8x7IGrCRcwuzQY0g'

log = logging.getLogger(__name__)


class ConfigureApp(object):

    def __init__(self, config):
        self.config = config

    def initialize(self):
        """
        Runs through config settings, creating resources if necessary
        :return: True on success, False on error
        """
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

    def prepare_local_storage(self):
        """
        Creates directory `savedir` for local filesystem save.
        :return:  True on success.
        """

        # check savedir, may be None
        if self.config.get('savedir', None) is None:
            log.info('savedir not set. Skipping.')
            return True

        savedir = abspath(self.config['savedir'])
        if not exists(savedir):
            log.warning('Save directory does not exist: {}. Creating'.format(savedir))
            makedirs(savedir)

        return True

    def prepare_working_directories(self):
        """
        Creates `workdir`, for staging file uploads. Must be set.
        :return: True on success.
        """
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

    def prepare_gdrive(self, credential_filename=None):
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

        ok = True

        gconfig = self.config.get('gdrive', None)
        if gconfig is None:
            return True

        credfname = credential_filename
        if credfname is None:
            credfname = 'google_auth.json'

        gfolder = self.config.get('gdrive', None)
        if gfolder is None:
            log.info('gdrive not set. Skipping.')
            return True

        if self.config.get('credential_folder') is None:
            log.error('credential_folder must be set.')
            ok = False

        creds_folder = abspath(self.config['credential_folder'])
        creds_file = abspath(join(creds_folder, credfname))

        log.info('Attempting authentication to GDrive')
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, creds_file)

        log.info('Searching for main folder {} on GDrive'.format(gfolder))

        gstorage = GDriveStorage(gauth, gfolder)

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
        if not exists(workdir):
            log.error('Working directory does not exist: {}'.format(workdir))
            ret = False

        # check savedir, may be None
        savedir = self.config.get('savedir', None)
        if savedir is not None and not exists(savedir):
            log.error('Save directory does not exist: {}'.format(savedir))
            ret = False

        camera = self.config.get('camera', None)
        if camera is None:
            log.error('Camera is required')
            ret = False

        # click forces a choice, but check it anyway
        res = self.config['resolution']

        if res != 'small' and res != '720p' and res != '1080p':
            log.error('Invalid resolution: {}'.format(res))
            ret = False

        return ret
