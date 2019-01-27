import logging
from time import sleep
from datetime import datetime

import multiprocessing

from multiprocessing import Process, Manager
from multiprocessing.pool import Pool
from multiprocessing.connection import wait

import numpy as np
import cv2

from MyPiEye.usbcamera import UsbCamera
from MyPiEye.motion_detect import MotionDetect, ImageCapture

from MyPiEye.multi.camera import camera_start, imgsave_start

import redis

# log = logging.getLogger(__name__)

log = multiprocessing.log_to_stderr()


class Supervisor(object):
    manager = None

    def __init__(self, config):

        self.config = config
        self.multi = config.get('multi', None)

        if self.multi is None:
            raise Exception('[multi] not found in configuration')

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

        sentinels = []

        if self.multi.get('enable_camera', False):
            # start the camera first
            cam_proc = Process(
                name='cam',
                target=camera_start,
                args=(self.config, img_obj))

            cam_proc.start()
            sentinels.append(cam_proc.sentinel)

            # and a process for saving to redis
            imgsave_proc = Process(
                name='imgsave',
                target=imgsave_start,
                args=(self.config, img_obj)
            )

            imgsave_proc.start()
            sentinels.append(imgsave_proc.sentinel)

        lsave = self.multi.get('local_save', None)
        if lsave is not None and str(lsave).strip() != '':
            # something for the webserver
            pass

        # compares images

        # motion_queue = Supervisor.manager.Queue()
        # motion_detect_proc = Process(
        #     name='imgcompare',
        #     target=Supervisor.motion_detect_proc,
        #     args=(self.config, img_obj, motion_queue)
        #  )

        sentinels = set(sentinels)

        while len(sentinels) > 0:
            done = set(wait(sentinels))
            if len(done) > 0:
                log.error('Process exited')
                sentinels = sentinels - done
            sleep(.05)


    @staticmethod
    def motion_detect_proc(config):
        motion_detect = MotionDetect(config)
        while True:
            sleep(1)

            # motion = motion_detect.motions(imgobj['imgbuf'])
            # if motion is not None:
            #     pass


