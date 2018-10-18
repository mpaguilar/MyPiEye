import logging
from os.path import exists, join, abspath

from MyPiEye.Storage.google_drive import GDriveAuth, GDriveStorage

CLIENT_ID = '990858881415-u53d5skorvuuq4hqjfj5pvq80d059744.apps.googleusercontent.com'
CLIENT_SECRET = '-9q0wn7j8x7IGrCRcwuzQY0g'

log = logging.getLogger(__name__)


class ConfigureApp(object):

    def __init__(self, config):
        self.config = config

        if self.config['gdrive'] is not None:
            assert self.config['credential_folder'] is not None, 'GDrive requires credential_folder'

            creds_file = abspath(join(self.config['credential_folder'], 'google_auth.json'))

            log.info('Attempting authentication to GDrive')
            gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, creds_file)

            log.info('Searching for main folder {} on GDrive'.format(self.config['gdrive']))

            log.info('Creating main folder on GDrive')
            ret = GDriveStorage.create_main_folder(gauth, self.config['gdrive'])

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
