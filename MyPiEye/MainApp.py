from os.path import dirname, basename, exists
import logging
import CLI

from usbcamera import UsbCamera

log = logging.getLogger(__name__)


class MainApp(object):

    def __init__(self, config):
        """
        The workhorse of the program.

        :param config: a dict of consolidated options (defaults, ini, cmdline)
        """

        self.config = config
        self.camera = UsbCamera(
            resolution=config['resolution'],
            camera=config['camera']
        )

    def start(self):



        self.camera.init_camera()

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

        # check gdrive
        # we may end up with multiple choices (OneDrive, Dropbox, et. al)
        # if so, this will have to change

        # TODO: a quick probe for connectivity
        gdrive = self.config.get('gdrive', None)
        if gdrive is None:
            log.error('GDrive is required')
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