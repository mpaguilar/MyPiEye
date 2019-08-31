import logging
from time import sleep
from datetime import datetime

import multiprocessing

from multiprocessing import Process, Manager
from multiprocessing.connection import wait

from MyPiEye.motion_detect import MotionDetect

from MyPiEye.multi.process_runners import camera_start, redis_start, azblob_start

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

        self.process_infos = {}

    def main_loop(self):
        running = True

        while running:

            for k in self.process_infos.keys():
                proc_info = self.process_infos[k]

                # if it's never been started or it's not running and it should be, then start it
                if (proc_info['process'] is None or (not proc_info['process'].is_alive())) \
                        and proc_info['run_process']:
                    log.warning('Starting {} process'.format(k))
                    proc_info['process'] = Process(**proc_info['process_args'])
                    proc_info['process'].start()
                    sleep(.5)

                # if it's running and shouldn't be, then kill it
                if (proc_info['process'] is not None and
                    proc_info['process'].is_alive()) and \
                        not proc_info['run_process']:

                    log.warning('Process {} is running, and should not be'.format(k))
                    log.warning('Shutting down process {}'.format(k))
                    proc_info['process'].kill()

            # block for up to five seconds
            sents = [self.process_infos[v]['process'].sentinel for v in self.process_infos.keys() if
                     self.process_infos[v]['run_process']]

            wait(sents, 5)

            sbrunning = len([v for v in self.process_infos.keys() if self.process_infos[v]['run_process']])
            isrunning = len([v for v in self.process_infos.keys() if
                             self.process_infos[v]['run_process'] and self.process_infos[v]['process'].is_alive()])

            # ready to exit
            if sbrunning == 0 and isrunning == 0:
                running = False
                continue

            # should be trying to exit
            if sbrunning == 0 and isrunning > 0:
                log.warning('Should be shutting down')

            # did everything crash?
            if sbrunning > 0 and isrunning == 0:
                log.error('Did everything crash?')

    def init_process_infos(self, img_obj: multiprocessing.Manager):

        if self.multi.get('enable_camera', False):
            # gotta have a camera
            self.process_infos['camera'] = {
                'process': None,
                'process_args': {
                    'name': 'cam',
                    'target': camera_start,
                    'args': (self.config, img_obj)
                },
                'run_process': True
            }

            # saving to redis
            self.process_infos['imgsave'] = {
                'process': None,

                'process_args': {
                    'name': 'imgsave',
                    'target': redis_start,
                    'args': (self.config, img_obj)
                },
                'run_process': False
            }
        if self.multi.get('enable_azure_blob', False):
            azconfig = self.config.get('azure_blob', None)
            if azconfig is not None:
                self.process_infos['azblob'] = {
                    'process': None,

                    'process_args': {
                        'name': 'azblob',
                        'target': azblob_start,
                        'args': (self.config, img_obj)
                    },
                    'run_process': True

                }
            else:
                log.error('azure_blob service requires [azure_blob] section')

    def start(self):
        log.info('Starting camera supervisor')
        Supervisor.manager = Manager()

        img_obj = Supervisor.manager.dict()
        # stores the current cv image as a list
        img_obj['imgbuf'] = Supervisor.manager.list()

        # so the camera can write
        img_obj['lock'] = Supervisor.manager.Lock()
        # so we don't stomp the network interface
        img_obj['netlock'] = Supervisor.manager.Lock()

        # a datetime object of the last capture, UTC
        img_obj['img_captured'] = datetime.utcnow()

        self.init_process_infos(img_obj)

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

        self.main_loop()

    @staticmethod
    def motion_detect_proc(config):
        motion_detect = MotionDetect(config)
        while True:
            sleep(1)

            # motion = motion_detect.motions(imgobj['imgbuf'])
            # if motion is not None:
            #     pass
