import cv2
import numpy as np
import logging
from time import sleep

log = logging.getLogger(__name__)


class UsbCamera(object):
    def __init__(self, resolution, camera=None):
        self.camera_id = camera
        self.camera = None
        self.is_open = False
        self.resolution = resolution

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
            raise Exception('Failed to open camera')


    def _init_camera(self):

        """
        Opens the video capture
        :return:
        True if the camera opens, or it isn't being used
        False if attempting to open the camera fails
        """

        if self.camera_id is not None:
            log.warning('Using camera {}'.format(self.camera_id))
            self.camera = cv2.VideoCapture(self.camera_id)
            x, y, fps = self.resolution
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, x)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, y)
            self.camera.set(cv2.CAP_PROP_FPS, fps)

            if not self.camera.isOpened():
                log.error('Failed to open camera')
                return False

            self.is_open = True
            x = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            y = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = self.camera.get(cv2.CAP_PROP_FPS)
            log.warning('x: {}, y: {}, fps: {}'.format(x, y, fps))

        return True

    def close_camera(self):
        if self.camera_id is not None and self.camera is not None:
            log.warning('Shutting down video capture')
            self.camera.release()
            del self.camera

    def get_image(self):

        if self.camera is not None:
            # log.debug('Reading from camera {}'.format(self.camera.isOpened()))
            ret, img = self.camera.read()
            if not ret:
                log.error('Failed to get camera image')
            return img
