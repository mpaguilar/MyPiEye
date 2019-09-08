from functools import partial
from datetime import datetime

from celery import Celery
from celery.utils.log import get_task_logger

from MyPiEye.Storage.minio_storage import MinioStorage
from MyPiEye.CLI import get_config_value

app = Celery('imghandler')
log = get_task_logger(__name__)

app_config = {}


@app.task()
def accept_capture(dt_stamp: datetime, cam_id: str):
    # bout-time/cam0/20190907/23/15/2019.09.07.23.15.49.220779.jpg

    log.info('Accepting capture')

    mio = MinioStorage(app_config)
    ret = mio.download_file('bout-time/cam0/20190907/23/15/2019.09.07.23.15.49.220779.jpg')
    log.debug(ret)

    return


@app.task()
def ping(txt):
    return '{}: pong!'.format(txt)
