import logging
from ast import literal_eval
from time import sleep
from os import remove
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
        self.executor = ProcessPoolExecutor(max_workers=2)

        self.storage = ImageStorage(fs_path=self.config['savedir'], gdrive_folder=self.config['gdrive'])

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

    def delete_tmp(self, fut):
        """
        Deletes tmp files. Should be attached to the future.

        :param fut: A future with `box_name` and `nobox_name` properties attached
        :return: None
        """

        error = fut.exception()
        if error:
            log.error('Error copying files')

        try:
            log.debug('Removing {}'.format(fut.box_name))
            remove(fut.box_name)
        except FileNotFoundError as fnfe:
            log.error('Could not delete file: {}'.format(fnfe.filename))

        try:
            log.debug('Removing {}'.format(fut.nobox_name))
            remove(fut.nobox_name)
        except FileNotFoundError as fnfe:
            log.error('Could not delete file: {}'.format(fnfe.filename))

    def store_files(self, box_name, nobox_name, capture_dt):
        """
        Sends file details to the executor.

        :param box_name: the path to the temporary annotated file
        :param nobox_name: the path to the temporary clean file
        :param capture_dt: a datetime when motion was detected
        :return: None
        """

        subdir = capture_dt.strftime('%y%m%d')

        self.storage.save_files(subdir, box_name, nobox_name)

        # res = self.executor.submit(
        #     save_files, self.config['savedir'], subdir=subdir, box_name=box_name, nobox_name=nobox_name)

        # res.box_name = box_name
        # res.nobox_name = nobox_name
        # res.add_done_callback(self.delete_tmp)

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
                self.store_files(box_name=box_name, nobox_name=nobox_name, capture_dt=capture_dt)

            sleep(.1)

        if retries >= 2:
            log.error('Failed to get image after {} attempts'.format(retries + 1))
