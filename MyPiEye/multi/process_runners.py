import multiprocessing
import logging

from time import sleep
from datetime import datetime

import redis
import cv2

from MyPiEye.usbcamera import UsbCamera
from MyPiEye.Storage.azure_blob import AzureBlobStorage

log = multiprocessing.log_to_stderr()


def camera_start(config, imgobj, internal_mq = None, external_mq = None):
    log.info('Starting camera')

    camera = None
    previous_image = None

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

        while ok:

            log.info('capturing {}'.format(datetime.utcnow()))
            img = camera.get_image()

            if img is not None:
                log.info('captured {}'.format(datetime.utcnow()))

                if log.level == logging.DEBUG:
                    # so it stands out
                    print('\ncaptured {}\n'.format(datetime.utcnow()))

                with imgobj['lock']:
                    imgobj['imgbuf'] = img
                    imgobj['img_captured'] = datetime.utcnow()

                log.info('captured image at {}'.format(datetime.utcnow()))
            else:
                log.error('Failed to get image')

            if time_delay > 0:
                sleep(time_delay)

    finally:
        if camera is not None:
            camera.close_camera()


def azblob_start(config, imgobj, internal_mq = None, external_mq = None):
    """
    Saves the current image to an Azure blob.
    The config should have a ``azure_blob`` section.
    set [multi] key ``azure_blob`` to ``True`` to enable.
    :param config:
    :param imgobj:
    :return:
    """

    azblob = AzureBlobStorage(config)
    if not azblob.configure():
        log.error('Failed to intialize Azure Blob storage')
        return

    last_captime: datetime = imgobj['img_captured']

    camconfig = config.get('camera', None)
    if camconfig is None:
        log.error('No camera config')
        return

    camid = camconfig.get('camera_id', 'unknown/unknown')

    while True:

        curdt: datetime = imgobj['img_captured']
        if curdt != last_captime:
            with imgobj['lock']:
                imgbuf = imgobj['imgbuf']

            (ok, jpg) = cv2.imencode('.jpg', imgbuf)

            if ok:
                fmt = azblob.config.get('filename_format', '%Y%m%d/%H%M%S.%f')
                dtstamp = curdt.isoformat()

                filename = '{}/{}.jpg'.format(camid, curdt.strftime(fmt))

                azblob.save(jpg, filename, dtstamp, camid)

            last_captime = curdt

        sleep(.1)


def redis_start(config, shared_obj):
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
