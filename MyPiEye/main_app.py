import logging
from ast import literal_eval
from time import sleep
from os.path import abspath
from concurrent.futures import ProcessPoolExecutor

from MyPiEye.Storage import ImageStorage
from MyPiEye.motion_detect import MotionDetect

from MyPiEye.usbcamera import UsbCamera

log = logging.getLogger(__name__)

"""
The workhorse of the program.
"""


class MainApp(object):

    def __init__(self, config):
        """
        :param config: a dict of consolidated options (defaults, ini, cmdline)
        """

        self.config = config

        # instanciates, but doesn't initialize
        camera_id = literal_eval(config['camera'])
        self.camera = UsbCamera(
            resolution=config['resolution'],
            camera=camera_id
        )

        # the camera can only be set from the .ini
        camera_settings = config.get('iniconfig', {})

        # convert the ini string key/val entries into a list of tuples
        ignore_dict = camera_settings.get('ignore', {})
        ignore_boxes = []

        for _, v in ignore_dict.items():
            val = literal_eval(v)
            ignore_boxes.append(val)

        # get the minimum sizes
        minsizes = camera_settings.get('minsizes', {})

        self.workdir = config['workdir']
        self.workdir = abspath(self.workdir)

        self.motiondetect = MotionDetect(
            workdir=self.workdir,
            # ini entries are always read as strings
            minsize=literal_eval(minsizes.get('minsize', '0')),
            ignore_boxes=ignore_boxes
        )

        # self.check should have ensured it exists
        self.savedir = config['savedir']
        self.executor = ProcessPoolExecutor(max_workers=2)

        self.storage = ImageStorage(config)

    def start(self):
        """
        Initializes the camera, and starts the main loop. Cleans up when it stops.

        :return: False on fail, True if the loop ends.
        """
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

        return True

    def save_images(self, cv_image, capture_dt, motions):
        """
        Saves CV2 image to various locations, with annotations.

        :param cv_image: CV2 image
        :param capture_dt: ``datetime``, UTC expected
        :param motions: list of box lists.
        :return:
        """
        ymd = capture_dt.strftime('%y%m%d')
        hms = capture_dt.strftime('%H%M%S.%f')
        dtstamp = capture_dt.strftime('%y/%m/%d %H:%M:%S.%f')

        # unaltered
        clean_fname = '{}/{}.{}.jpg'.format(self.workdir, ymd, hms)
        MotionDetect.save_cv_image(cv_image, clean_fname)
        log.info('Saved {}'.format(clean_fname))

        # timestamp
        ts_fname = '{}/{}.{}.ts.jpg'.format(self.workdir, ymd, hms)
        ts_image = MotionDetect.add_timestamp(cv_image, dtstamp)
        MotionDetect.save_cv_image(ts_image, ts_fname)
        log.info('Saved {}'.format(ts_fname))

        # fully annotated
        full_fname = '{}/{}.{}.box.jpg'.format(self.workdir, ymd, hms)
        full_image = MotionDetect.add_motion_boxes(ts_image, motions)
        MotionDetect.save_cv_image(full_image, full_fname)
        log.info('Saved {}'.format(full_fname))

        return clean_fname, ts_fname, full_fname

    def watch_for_motions(self):
        """
        Main loop for watching for changes

        :return: Yields tuple of changes
        """

        retries = 0

        while True and retries < 3:
            # Note: this is a CV2 image.
            current_img = self.camera.get_image()
            if current_img is None:
                log.error('Failed to get image')
                sleep(1)
                retries += 1
                continue

            retries = 0

            motion = self.motiondetect.motions(current_img)

            if motion is not None:
                log.debug('Motion detected.')

                capture_dt, movements = motion

                # save processed images to temp files
                files = self.save_images(current_img, capture_dt, movements)

                # store the temp files in their permanent locations
                subdir = capture_dt.strftime('%y%m%d')
                self.storage.save_files(subdir, files[2], files[1], capture_dt)

            else:
                # nothing to do, so goof off a fraction of a second
                sleep(.1)

        if retries >= 2:
            log.error('Failed to get image after {} attempts'.format(retries + 1))
