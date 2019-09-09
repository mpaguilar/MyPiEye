from functools import partial
from datetime import datetime

from io import BytesIO

import numpy as np
import pickle

from celery import Celery
from celery.utils.log import get_task_logger

from MyPiEye.Storage.minio_storage import MinioStorage
from MyPiEye.CLI import get_config_value

celery_app = Celery('imghandler')
celery_app.config_from_object({
    'task_serializer': 'pickle',
    'accept_content' : ['json', 'pickle']
})
log = get_task_logger(__name__)

app_config = {}


@celery_app.task()
def accept_capture(img_bytes, dt_stamp: datetime, cam_id: str):
    # bout-time/cam0/20190907/23/15/2019.09.07.23.15.49.220779.jpg

    log.info('Accepting capture')

    cv2img = pickle.loads(img_bytes)

    mio = MinioStorage(app_config)
    mio.upload(cv2img, dt_stamp, cam_id)

    log.info('Uploaded')



@celery_app.task()
def ping(txt):
    log.info('Received ping')
    return '{}: pong!'.format(txt)
