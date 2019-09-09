from os import environ
import logging
from functools import partial
from time import sleep
from datetime import datetime

from io import BytesIO

import numpy as np

from MyPiEye.CeleryTasks import celery_app
import MyPiEye.CeleryTasks as mycel

from MyPiEye.CLI import get_config_value

log = logging.getLogger()


class CeleryStorage(object):
    def __init__(self, global_config):
        self.cfg = partial(get_config_value, global_config, 'celery')
        self.host = self.cfg('host', 'CELERY_REDIS_HOST')
        self.port = int(self.cfg('port', 'CELERY_REDIS_PORT', '6379'))
        self.db = int(self.cfg('db', 'CELERY_REDIS_DB', '0'))

        self.camid = get_config_value(global_config, 'camera', 'camera_id', 'CAMERA_ID', 'unknown/unknown')

        self.redis_url = f'redis://{self.host}:{self.port}/{self.db}'

        celery_app.conf.broker_url = self.redis_url
        celery_app.conf.result_backend = self.redis_url

    def check(self):
        ret = True
        if self.host is None:
            log.error('host is not set')
            ret = False

        if self.port is None:
            log.error('port is not set')
            ret = False

        if self.db is None:
            log.error('db is not set')
            ret = False

        if self.camid is None:
            log.error('camid is not set')
            ret = False

        return ret

    def configure(self):
        return True

    def start(self, shared_obj, shared_lock, storage_queues: dict):
        pri_storage_queue = storage_queues.get('celery')
        if pri_storage_queue is None:
            log.error('No message queue for celery')
            sleep(1)
            return

        while True:

            # blocks until a message is ready
            dt_pic = pri_storage_queue.get()

            log.info('processing incoming capture')

            # block until it's not in use
            with shared_lock:
                curdt: datetime = shared_obj['img_captured']
                imgbuf = shared_obj['imgbuf']

                # if the current image datetime doesn't match the message
                # then this message is stale. We can skip it and pull the next.
                if curdt != dt_pic['dt']:
                    log.info('Skipping stale message')
                    continue

                log.info('Sending message to celery worker: {}'.format(curdt.isoformat()))
                self.upload(imgbuf, curdt)

    def upload(self, cv2_imgbytes, dt_stamp):

        imgstr = cv2_imgbytes.dumps()

        mycel.accept_capture.delay(imgstr, dt_stamp, self.camid)
