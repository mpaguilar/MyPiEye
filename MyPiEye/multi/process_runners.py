import multiprocessing
import logging

from time import sleep
from datetime import datetime

import redis
import cv2

from MyPiEye.usbcamera import UsbCamera
from MyPiEye.Storage.azure_blob import AzureBlobStorage
from MyPiEye.Storage.minio_storage import MinioStorage

from MyPiEye.CLI import get_config_value

log = logging.getLogger(__name__)
# log.setLevel(logging.DEBUG)


def camera_start(config, shared_obj, msg_queues: dict):
    """

    :param config: The global config
    :param shared_obj: Where to store the pics and metadata
    :param msg_queues: Queues to notify when a picture is ready
    :return:
    """
    log.info('Starting camera')

    camera = None

    cam_config = config.get('camera', None)
    if cam_config is None:
        log.error('No [camera] config section found')
        sleep(1)
        return

    time_delay = cam_config.get('time_delay', '0')
    time_delay = int(time_delay)

    try:
        camera = UsbCamera(config)
        ok = camera.init_camera()

        log.info('Starting camera loop')
        while ok:

            log.debug('capturing {}'.format(datetime.utcnow()))
            img = camera.get_image()

            if img is not None:
                dtsrt = datetime.now()

                # with shared_obj['lock']:
                log.debug('captured {}'.format(dtsrt))

                if log.level == logging.DEBUG:
                    # so it stands out
                    print('\ncaptured {}\n'.format(dtsrt))

                with shared_obj['lock']:
                    shared_obj['imgbuf'] = img
                    shared_obj['img_captured'] = dtsrt

                for val in msg_queues.values():
                    try:
                        val.put({'dt': dtsrt}, False)
                    except Exception as e:
                        log.warning('Skipping frame for queue')
                        continue

                log.info('captured image at {}'.format(dtsrt))
            else:
                log.error('Failed to get image')

            if time_delay > 0:
                sleep(time_delay)

    finally:
        if camera is not None:
            camera.close_camera()


def minio_start(config, shared_obj, storage_queues: dict):
    pri_storage_queue = storage_queues.get('minio')
    if pri_storage_queue is None:
        log.error('No message queue for minio')
        sleep(1)
        return

    mio = MinioStorage(config)

    if not mio.check():
        log.error('Failed to initialize minio storage')
        return

    camid = get_config_value(config, 'camera', 'camera_id', 'CAMERA_ID', 'unknown/unknown')

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

        log.debug('Storing image {}'.format(curdt.isoformat()))

        (ok, jpg) = cv2.imencode('.jpg', imgbuf)

        if ok:
            mio.upload(jpg, curdt, camid)

        sleep(.01)

def local_start(config, shared_obj, storage_queues: dict):
    storage_q = storage_queues.get('local')
    if storage_q is None:
        log.error('No queue found for local storage')
        sleep(1)
        return

    camid = get_config_value(config, 'camera', 'camera_id', 'CAMERA_ID', 'unknown/unknown')






def azblob_start(config, shared_obj, **kwargs):
    """
    Saves the current image to an Azure blob.
    The config should have a ``azure_blob`` section.
    set [multi] key ``azure_blob`` to ``True`` to enable.

    This one just goes as fast as it can. It doesn't use a queue.

    :param config:
    :param shared_obj:
    :param kwargs: Ignored.
    :return:
    """

    azblob = AzureBlobStorage(config)
    if not azblob.check():
        log.error('Failed to intialize Azure Blob storage')
        return

    last_captime: datetime = shared_obj['img_captured']

    camconfig = config.get('camera', None)
    if camconfig is None:
        log.error('No camera config')
        return

    camid = camconfig.get('camera_id', 'unknown/unknown')

    while True:

        curdt: datetime = shared_obj['img_captured']
        if curdt != last_captime:
            with shared_obj['lock']:
                imgbuf = shared_obj['imgbuf']

            (ok, jpg) = cv2.imencode('.jpg', imgbuf)

            if ok:
                azblob.upload(jpg, curdt, camid)

            last_captime = curdt

        sleep(.1)


def redis_start(config, shared_obj, storage_queues: dict):
    """
    Saves the current image to a file, for a webserver
    :param config: Global config
    :param shared_obj: Shared current image
    :return:
    """
    try:
        log.info('running redis')
        rconfig = config.get('redis', None)

        if not rconfig:
            log.error('No [redis] config section found')
            sleep(1)
            return

        if rconfig.get('server_name', None) is None:
            log.error('Missing server_name in [redis] section')
            sleep(1)
            return

        rds = redis.Redis(host=rconfig['server_name'])
        print(rds.get('foo'))
        last_captime: datetime = shared_obj['img_captured']

        while True:
            curdt: datetime = shared_obj['img_captured']
            if curdt != last_captime:
                with shared_obj['lock']:
                    imgbuf = shared_obj['imgbuf']

                (ok, jpg) = cv2.imencode('.jpg', imgbuf)

                if ok:
                    camid = config.get('camera_id', 'unknown/unknown')
                    dtstamp = last_captime.strftime('%Y%m%d/%H%M%S.%f')
                    rkey = 'raw/{}/{}'.format(camid, dtstamp)

                    with shared_obj['netlock']:
                        log.info('Sending data to redis')
                        rds.set(rkey, jpg.tostring())
            sleep(.05)
    except Exception as e:
        log.critical('Critical failure in imgsave')
        log.critical(e)
