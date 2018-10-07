from os.path import dirname, basename, exists
import logging
import CLI
from motion_detect import MotionDetect

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

    def watch_for_motions(self):
        """
        Main loop for watching for changes

        :return: Yields tuple of changes
        """

        try:

            md = MotionDetect(workdir=self.workdir, show_timings=self.show_timings)

            while True:

                cfg = config(self.ini_file)
                md.set_ignore(int(cfg['minsize']), cfg['ignore'], cfg['min_height'], cfg['min_width'])

                if not os.path.exists(self.workdir):
                    os.makedirs(self.workdir)

                current_img = self.imgread.get_image()
                if current_img is None:
                    log.error('Failed to get image')
                    sleep(1)
                    continue

                motion, dtstamp, nobox_name, box_name, movements = md.motions(
                    current_img)

                if motion:
                    yield (dtstamp, nobox_name, box_name, movements)
                    # sleep(.3)

                sleep(.1)
        finally:
            log.warning('Shutting down queue')
            self.file_queue.put(None)
            self.imgread.close_camera()
