import logging
from time import sleep
from datetime import datetime

import multiprocessing

from multiprocessing import Process, Manager
from multiprocessing.connection import wait

from MyPiEye.motion_detect import MotionDetect

from MyPiEye.multi.process_runners import \
    local_start, \
    camera_start, \
    redis_start, \
    azblob_start, \
    minio_start, \
    celery_start

from MyPiEye.CLI import get_self_config_value

log = multiprocessing.log_to_stderr()


class Supervisor(object):
    manager = None

    def __init__(self, config):

        self.config = config
        self.self_config = config.get('multi', None)

        if self.self_config is None:
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


    def init_process_infos(self,
                           shared_obj: multiprocessing.Manager):

        storage_queues = {}

        def init_proc(proc_name: str, proc_func, run=True):
            self.process_infos[proc_name] = {
                'process': None,
                'process_args': {
                    'name': proc_name,
                    'target': proc_func,
                    'args': (self.config, shared_obj, storage_queues)
                },
                'run_process': run
            }

        if get_self_config_value(self, 'enable_camera', 'MULTI_ENABLE_CAMERA', False):
            init_proc('camera', camera_start, True)

        storage_proc_count = self.config['multi'].get('backend_processes', '1')
        storage_proc_count = int(storage_proc_count)

        for x in range(1, storage_proc_count + 1):

            if get_self_config_value(
                    self, 'enable_redis', 'MULTI_REDIS', False) in [True, 'True']:
                storage_queues['redis'] = multiprocessing.Queue(maxsize=1)
                init_proc('redis_{}'.format(x), redis_start, True)

            if get_self_config_value(
                    self, 'enable_azure_blob', 'MULTI_AZBLOB', False) in [True, 'True']:
                storage_queues['azure'] = multiprocessing.Queue(maxsize=1)
                init_proc('azblob_{}'.format(x), azblob_start, True)

            if get_self_config_value(
                    self, 'enable_minio', 'MULTI_MINIO', False) in [True, 'True']:
                storage_queues['minio'] = multiprocessing.Queue(maxsize=1)
                init_proc('minio_{}'.format(x), minio_start, True)

            if get_self_config_value(
                    self, 'enable_local', 'MULTI_LOCAL', False) in [True, 'True']:
                storage_queues['minio'] = multiprocessing.Queue(maxsize=1)
                init_proc('local_{}'.format(x), local_start, True)

            if get_self_config_value(
                    self, 'enable_celery', 'MULTI_CELERY', False) in [True, 'True']:
                storage_queues['celery'] = multiprocessing.Queue(maxsize=1)
                init_proc('celery_{}'.format(x), celery_start, True)

    def start(self):
        log.info('Starting camera supervisor')
        Supervisor.manager = Manager()
        msgqueues = {}

        shared_obj = Supervisor.manager.dict()
        # stores the current cv image as a list
        shared_obj['imgbuf'] = Supervisor.manager.list()

        # so the camera can write in peace.
        shared_obj['lock'] = Supervisor.manager.Lock()

        # used by services copying to local networks
        # so that the network interface isn't swamped
        # WAN-bound services don't need it.
        shared_obj['netlock'] = Supervisor.manager.Lock()

        # a datetime object of the last capture, UTC
        shared_obj['img_captured'] = datetime.utcnow()

        self.init_process_infos(shared_obj);

        # compares images

        # motion_queue = Supervisor.manager.Queue()
        # motion_detect_proc = Process(
        #     name='imgcompare',
        #     target=Supervisor.motion_detect_proc,
        #     args=(self.config, shared_obj, motion_queue)
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
