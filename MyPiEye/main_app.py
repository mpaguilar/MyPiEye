import logging
from datetime import datetime
from time import sleep
from os.path import abspath
from concurrent.futures import ProcessPoolExecutor

from MyPiEye.Storage import ImageStorage
from MyPiEye.motion_detect import MotionDetect, ImageCapture

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
        self.camera = UsbCamera(config)

        self.workdir = abspath(config['workdir'])

        self.motiondetect = MotionDetect(
            config
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

    def save_images(self, motion: ImageCapture):
        """
        Saves CV2 image to various locations, with annotations.

        :param motion: an ImageCapture object with at least capture_dt, clean_image, and motions populated.
        :return: an ImageCapture object (the same one) with temp file names populated
        """

        # unaltered
        log.info('Saving clean image')
        start_time = datetime.now()
        motion.clean_fname = '{}/{}.jpg'.format(self.workdir, motion.base_filename)
        MotionDetect.save_cv_image(motion.clean_image, motion.clean_fname)
        end_time = datetime.now()
        tot_time = end_time - start_time
        log.info('Saved tmpfile ({}) {}'.format(tot_time, motion.clean_fname))

        # timestamp
        log.info('Saving timestamp image')
        start_time = datetime.now()
        motion.ts_fname = '{}/{}.ts.jpg'.format(self.workdir, motion.base_filename)
        motion.ts_image = MotionDetect.add_timestamp(motion.clean_image, motion.timestamp_utc)
        MotionDetect.save_cv_image(motion.ts_image, motion.ts_fname)
        end_time = datetime.now()
        tot_time = end_time - start_time
        log.info('Saved tmpfile ({}) {}'.format(tot_time, motion.ts_fname))

        # fully annotated
        log.info('Saving full annotated image')
        start_time = datetime.now()
        motion.full_fname = '{}/{}.box.jpg'.format(self.workdir, motion.base_filename)
        motion.full_image = MotionDetect.add_motion_boxes(motion.ts_image, motion.motions)
        MotionDetect.save_cv_image(motion.full_image, motion.full_fname)
        end_time = datetime.now()
        tot_time = end_time - start_time
        log.info('Saved tmpfile ({}) {}'.format(tot_time, motion.full_fname))

        return motion

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

                # the object only has motion object right now.
                motion.clean_image = current_img

                # process and save temp images
                files = self.save_images(motion)

                # store the temp files in their permanent locations
                self.storage.save_files(motion)

            else:
                # nothing to do, so goof off a fraction of a second
                sleep(.1)

        if retries >= 2:
            log.error('Failed to get image after {} attempts'.format(retries + 1))
