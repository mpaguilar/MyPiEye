import logging
from time import sleep
from datetime import datetime

import multiprocessing

from multiprocessing import Process, Manager
from multiprocessing.connection import wait

from MyPiEye.motion_detect import MotionDetect

from MyPiEye.multi.camera import camera_start, imgsave_start

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

        # sentinels = []
        process_infos = {}

        if self.multi.get('enable_camera', False):
            # start the camera first
            cam_proc = Process(
                name='cam',
                target=camera_start,
                args=(self.config, img_obj))

            # cam_proc.start()
            # process_infos.append(cam_proc.sentinel)
            process_infos['camera'] = {
                'process' : cam_proc,
                'process_args': {
                    'name': 'cam',
                    'target': camera_start,
                    'args': (self.config, img_obj)
                },
                'run_process': True
            }

            # and a process for saving to redis
            imgsave_proc = Process(
                name='imgsave',
                target=imgsave_start,
                args=(self.config, img_obj)
            )

            # imgsave_proc.start()
            # process_infos.append(imgsave_proc.sentinel)
            process_infos['imgsave'] = {
                'process' : imgsave_proc,

                'process_args': {
                    'name': 'imgsave',
                    'target': imgsave_start,
                    'args': (self.config, img_obj)
                },
                'run_process' : True
            }

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

        # the first time through, nothing will be running
        # it is reset after the first pass
        running = True


        while running: # len(sents) > 0:

            for k in process_infos.keys():
                proc_info = process_infos[k]

                if not proc_info['process'].is_alive():
                    log.warning('The {} process is not running'.format(k))

                if (not proc_info['process'].is_alive()) and proc_info['run_process']:
                    log.warning('Starting {} process'.format(k))
                    proc_info['process'] = Process(
                        **proc_info['process_args'])
                    proc_info['process'].start()
                    sleep(.5)

                if (proc_info['process'].is_alive()) and not proc_info['run_process']:
                    log.warning('Process {} is running, and should not be'.format(k))
                    log.warning('Shutting down process {}'.format(k))
                    proc_info['process'].kill()

            sents = [process_infos[v]['process'].sentinel for v in process_infos.keys() if process_infos[v]['run_process']]
            wait(sents)

            sbrunning = [process_infos[v]['run_process'] for v in process_infos.keys()]
            if len(sbrunning) == 0:
                running = False


    @staticmethod
    def motion_detect_proc(config):
        motion_detect = MotionDetect(config)
        while True:
            sleep(1)

            # motion = motion_detect.motions(imgobj['imgbuf'])
            # if motion is not None:
            #     pass
