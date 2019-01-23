import logging
from time import sleep
from datetime import datetime

import multiprocessing

from multiprocessing import Process, Manager
from multiprocessing.pool import Pool

import numpy as np
import cv2

from MyPiEye.usbcamera import UsbCamera
from MyPiEye.motion_detect import MotionDetect, ImageCapture

# log = logging.getLogger(__name__)

log = multiprocessing.log_to_stderr()


class Supervisor(object):
    manager = None

    def __init__(self, config):

        self.config = config

        self.compare_proc = None

        self.upload_pool = None

    def start(self):
        log.info('Starting camera supervisor')
        Supervisor.manager = Manager()

        img_obj = Supervisor.manager.dict()
        # stores the current cv image as a list
        img_obj['imgbuf'] = Supervisor.manager.list()
        # a datetime object of the last capture, UTC
        img_obj['img_captured'] = datetime.utcnow()



        # start the camera first
        cam_proc = Process(
            name='cam',
            target=Supervisor.start_camera,
            args=(self.config, img_obj))

        cam_proc.start()

        # something for the webserver
        imgsave_proc = Process(
            name='imgsave',
            target=Supervisor.start_imgsave,
            args=(self.config, img_obj)
        )

        # compares images

        motion_queue = Supervisor.manager.Queue()
        motion_detect_proc = Process(
            name='imgcompare',
            target=Supervisor.start_motion_detect,
            args=(self.config, img_obj, motion_queue)
        )

        imgsave_proc.start()

        cam_proc.join()
        imgsave_proc.join()


    @staticmethod
    def start_imgsave(config, imgobj):
        """
        Saves the current image to a file, for a webserver
        :param config: Global config
        :param imgobj: Shared current image
        :return:
        """
        log.info('saving image')
        last_captime = imgobj['img_captured']

        while True:
            curdt = imgobj['img_captured']
            if curdt != last_captime:
                imgbuf = imgobj['imgbuf']
                cv2.imwrite('tmp/blah.jpg', imgbuf)
            sleep(.05)

    @staticmethod
    def start_motion_detect(config, imgobj):
        motion_detect = MotionDetect(config)
        while True:

            motion = motion_detect.motions(imgobj['imgbuf'])
            if motion is not None:
                pass

    @staticmethod
    def start_camera(config, imgobj):
        log.info('Starting camera')

        camera = None

        try:
            camera = UsbCamera(config)
            ok = camera.init_camera()

            while ok:

                imgevt = imgobj['img_ready']
                # imgevt.clear()

                print('capturing {}'.format(datetime.utcnow()))
                img = camera.get_image()

                if img is not None:
                    print('captured {}'.format(datetime.utcnow()))
                    imgobj['imgbuf'] = img
                    imgobj['img_captured'] = datetime.utcnow()
                    print('stored {}'.format(datetime.utcnow()))
                else:
                    log.error('Failed to get image')

                # imgevt.set()

        finally:
            if camera is not None:
                camera.close_camera()
