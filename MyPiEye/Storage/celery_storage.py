from os import environ
import logging
from functools import partial
from time import sleep
from datetime import datetime

from MyPiEye.CeleryTasks import app
import MyPiEye.CeleryTasks as mycel

from MyPiEye.CLI import get_config_value

log = logging.getLogger()


class CeleryStorage(object):
    def __init__(self, global_config):
        self.cfg = partial(get_config_value, global_config, 'celery')
        self.host = self.cfg('host', 'CELERY_REDIS_HOST')
        self.port = int(self.cfg('post', 'CELERY_REDIS_PORT', '6379'))
        self.db = int(self.cfg('db', 'CELERY_REDIS_DB', '0'))

        self.camid = get_config_value(global_config, 'camera', 'camera_id', 'CAMERA_ID', 'unknown/unknown')

        self.redis_url = f'redis://{self.host}:{self.port}/{self.db}'

        app.conf.broker_url = self.redis_url
        app.conf.result_backend = self.redis_url

    def check(self):
        return True

    def configure(self):
        return True

    def start(self, shared_obj, storage_queues: dict):
        pri_storage_queue = storage_queues.get('celery')
        if pri_storage_queue is None:
            log.error('No message queue for celery')
            sleep(1)
            return

        while True:

            # blocks until a message is ready
            dt_pic = pri_storage_queue.get()
            with shared_obj['lock']:
                curdt: datetime = shared_obj['img_captured']
                imgbuf = shared_obj['imgbuf']

            # if the current image datetime doesn't match the message
            # then this message is stale. We can skip it and pull the next.
            if curdt != dt_pic['dt']:
                continue

            log.debug('Storing image on minio: {}'.format(curdt.isoformat()))

            self.upload(imgbuf, curdt)

            sleep(.01)

    def upload(self, cv2_imgbuf, dt_stamp):
        ret = mycel.ping.delay('ping').get()

        print(ret)


