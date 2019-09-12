from functools import partial
from datetime import datetime

import pickle
import json
import pytz

from celery import Celery
from celery.utils.log import get_task_logger

import redis

from MyPiEye.Storage.minio_storage import MinioStorage
from MyPiEye.CLI import get_config_value

celery_app = Celery('imghandler')
celery_app.config_from_object({
    'task_serializer': 'pickle',
    'accept_content': ['json', 'pickle']
})
log = get_task_logger(__name__)

# this has to be set to the global config on initialization of celery_app
app_config = {}


@celery_app.task()
def store_capture(img_bytes, dt_stamp: datetime, cam_id: str):
    # bout-time/cam0/20190907/23/15/2019.09.07.23.15.49.220779.jpg

    log.info('Storing capture to minio')

    cv2img = pickle.loads(img_bytes)

    mio = MinioStorage(app_config)
    mio.upload(cv2img, dt_stamp, cam_id)

    log.info('Stored {} capture to minio'.format(dt_stamp.isoformat()))


@celery_app.task()
def register_capture(dt_stamp: datetime, cam_id: str):

    log.warning('Adding capture to redis db')
    rcfg = partial(get_config_value, app_config, 'db_redis')

    redis_host = rcfg('host', 'DB_REDIS_HOST')
    redis_port = rcfg('port', 'DB_REDIS_PORT')
    redis_db = rcfg('db', 'DB_REDIS_DB')

    redis_password = rcfg('password', 'DB_REDIS_PASSWORD')
    timezone = get_config_value(app_config, 'global', 'timezone', 'TIMEZONE', 'US/Central')

    redis_prefix = rcfg('db_prefix', 'DB_REDIS_PREFIX')

    rsrv = redis.Redis(redis_host, redis_port, redis_db, redis_password)
    fmt = '%Y%m%d/%H/%M/%Y.%m.%d.%H.%M.%S.%f'
    key = '{}/{}/{}'.format(redis_prefix, cam_id, dt_stamp.strftime(fmt))

    tz = pytz.timezone(timezone)
    local_time = tz.localize(dt_stamp)

    val = {
        'utc_time': dt_stamp.isoformat(timespec='microseconds'),
        'local_time': local_time.isoformat(timespec='microseconds'),
        'camera_id': cam_id
    }

    val = json.dumps(val)

    ret = rsrv.set(key, val)
    log.warn('Redis updated with {}'.format(dt_stamp.isoformat()))


@celery_app.task()
def ping(txt):
    log.info('Received ping')
    return '{}: pong!'.format(txt)
