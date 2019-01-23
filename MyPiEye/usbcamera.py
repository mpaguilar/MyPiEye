import cv2
import logging
from time import sleep
from ast import literal_eval

log = logging.getLogger(__name__)


class UsbCamera(object):
    def __init__(self, config):
        self.config = config
        self.cam_config = config.get('camera', None)

        self.camera_id = self.cam_config.get('camera', None)
        self.camera_id = literal_eval(self.camera_id)

        self.camera_instance = None
        self.is_open = False

        resolution = self.cam_config['resolution']

        # the size of the raw image array
        self.img_size = 0

        if resolution == '1080p':
            self.resolution = (1920, 1080, 26)
        elif resolution == '720p':
            self.resolution = (1280, 720, 26)
        elif resolution == 'small':
            self.resolution = (640, 480, 26)
        else:
            self.resolution = None

        if self.resolution is not None:
            self.img_size = self.resolution[0] * self.resolution[1]

    def check(self):
        ret = True

        if self.cam_config is None:
            log.error('[camera] section is required is required')
            # we won't have keys if there's no section
            return False

        if self.camera_id is None:
            log.error('camera_id is required')
            ret = False

        if self.resolution is None:
            log.error('resolution is required')
            ret = False

        return ret

    def init_camera(self):
        """
        Attempts to open the camera. Retries three times, every five seconds.
        Throws an exception on failure.
        :return: None
        """
        camopen = self._init_camera()
        retry = 0

        while not camopen and retry < 3:
            log.warning('Failed to open camera. Retrying in 5 seconds')
            self.close_camera()
            retry = retry + 1
            sleep(5)
            camopen = self._init_camera()

        if retry >= 3:
            return False

        return True

    def _init_camera(self, orig=True):

        """
        Opens the video capture
        :return:
        True if the camera opens, or it isn't being used
        False if attempting to open the camera fails
        """

        if orig:
            log.info('Using OpenCV version {}.{}'.format(cv2.getVersionMajor(), cv2.getVersionMinor()))

            if self.camera_id is not None:
                log.info('Using camera {}'.format(self.camera_id))
                self.camera_instance = cv2.VideoCapture(self.camera_id)

                x, y, fps = self.resolution
                self.camera_instance.set(cv2.CAP_PROP_FRAME_WIDTH, x)
                self.camera_instance.set(cv2.CAP_PROP_FRAME_HEIGHT, y)
                self.camera_instance.set(cv2.CAP_PROP_FPS, fps)

                if not self.camera_instance.isOpened():
                    log.error('Failed to open camera')
                    return False

                self.is_open = True
                x = self.camera_instance.get(cv2.CAP_PROP_FRAME_WIDTH)
                y = self.camera_instance.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = self.camera_instance.get(cv2.CAP_PROP_FPS)
                log.warning('x: {}, y: {}, fps: {}'.format(x, y, fps))

            return True

    def close_camera(self):
        if not hasattr(self, 'camera'):
            return

        if self.camera_id is not None and self.camera_instance is not None:
            log.warning('Shutting down video capture')
            self.camera_instance.release()
            del self.camera_instance

    def get_image(self):
        """
        Get the current OpenCV image off the camera
        :return:
        """

        if self.camera_instance is not None:
            # log.debug('Reading from camera {}'.format(self.camera.isOpened()))
            ret, img = self.camera_instance.read()
            if not ret:
                log.error('Failed to get camera image')
                return None
            return img
        else:
            log.error('Camera not initialized')
            return None

    @staticmethod
    def save_image(cv_image, filename):
        """
        Write the OpenCV image as a file.

        :param cv_image: an OpenCV image array
        :param filename:
        :return:
        """
        cv2.imwrite(filename, cv_image)
