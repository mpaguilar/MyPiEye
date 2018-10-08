from os.path import exists
import logging
from motion_detect import MotionDetect
from ast import literal_eval
from time import sleep
import datetime

from storage import local_save

from concurrent.futures import ProcessPoolExecutor

from usbcamera import UsbCamera

log = logging.getLogger(__name__)


class MainApp(object):

    def __init__(self, config):
        """
        The workhorse of the program.

        :param config: a dict of consolidated options (defaults, ini, cmdline)
        """

        self.config = config

        # instanciates, but doesn't initialize
        camera_id = literal_eval(config['camera'])
        self.camera = UsbCamera(
            resolution=config['resolution'],
            camera=camera_id
        )

        camera_settings = config.get('iniconfig', {})

        # convert the ini string key/val entries into a list of tuples
        ignore_dict = camera_settings.get('ignore', {})
        ignore_boxes = []

        for _, v in ignore_dict.items():
            val = literal_eval(v)
            ignore_boxes.append(val)

        # get the minimum sizes
        minsizes = camera_settings.get('minsizes', {})

        self.motiondetect = MotionDetect(
            workdir=config['workdir'],
            # ini entries are always read as strings
            minsize=literal_eval(minsizes.get('minsize', '0')),
            ignore_boxes=ignore_boxes
        )

        # self.check should have ensured it exists
        self.savedir = config['savedir']
        # self.fileupload = FileUpload(savedir=savedir)
        self.executor = ProcessPoolExecutor(max_workers=2)

    def start(self):
        try:
            if not self.camera.init_camera():
                log.error('Failed to open camera')
                return False

            self.watch_for_motions()
        finally:
            log.warning('Shutting down')
            self.camera.close_camera()
            log.warning('Waiting on external process shutdown')
            self.executor.shutdown()

    def save_files(self, box_name, nobox_name, capture_dt):
        """
        Sends file details to the executor
        :param box_name: the path to the temporary annotated file
        :param nobox_name: the path to the temporary clean file
        :param capture_dt: a datetime when motion was detected
        :return: None
        """

        if self.config.get('savedir', False):
            subdir = capture_dt.strftime('%y%m%d')

            fut = self.executor.submit(
                local_save, self.config['savedir'], box_name, nobox_name, subdir)

            box_path, nobox_path = fut.result()

            log.debug('Saved box to {}'.format(box_path))
            log.debug('Saved nobox to {}'.format(nobox_path))

    def watch_for_motions(self):
        """
        Main loop for watching for changes

        :return: Yields tuple of changes
        """

        retries = 0

        while True and retries < 3:
            current_img = self.camera.get_image()
            if current_img is None:
                log.error('Failed to get image')
                sleep(1)
                retries += 1
                continue

            retries = 0

            motion, capture_dt, nobox_name, box_name, movements = self.motiondetect.motions(
                current_img)

            if motion:
                # yield (dtstamp, nobox_name, box_name, movements)
                log.debug('image captured')
                self.save_files(box_name=box_name, nobox_name=nobox_name, capture_dt=capture_dt)

            sleep(.1)

        if retries >= 2:
            log.error('Failed to get image after {} attempts'.format(retries + 1))

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
        # currently unused
        # gdrive = self.config.get('gdrive', None)
        # if gdrive is None:
        #     log.error('GDrive is required')
        #     ret = False
        log.warning('*** GDrive is disabled')

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
