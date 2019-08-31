import multiprocessing

from time import sleep
from datetime import datetime

import redis

from MyPiEye.usbcamera import UsbCamera

log = multiprocessing.log_to_stderr()

def camera_start(config, imgobj):
    log.info('Starting camera')

    camera = None

    try:
        camera = UsbCamera(config)
        ok = camera.init_camera()

        while ok:

            print('capturing {}'.format(datetime.utcnow()))
            img = camera.get_image()

            if img is not None:
                print('captured {}'.format(datetime.utcnow()))
                imgobj['imgbuf'] = img
                imgobj['img_captured'] = datetime.utcnow()
                print('stored {}'.format(datetime.utcnow()))
            else:
                log.error('Failed to get image')

            sleep(100)

    finally:
        if camera is not None:
            camera.close_camera()

def imgsave_start(config, imgobj):
    """
    Saves the current image to a file, for a webserver
    :param config: Global config
    :param imgobj: Shared current image
    :return:
    """
    try:
        log.info('saving image')
        last_captime: datetime = imgobj['img_captured']

        rds = redis.Redis(host='bigbox.node.home.mpa')
        print(rds.get('foo'))

        while True:
            curdt: datetime = imgobj['img_captured']
            if curdt != last_captime:
                imgbuf = imgobj['imgbuf']
                (ok, jpg) = cv2.imencode('.jpg', imgbuf)

                if ok:
                    camid = config.get('camera_id', 'unknown/unknown')
                    dtstamp = last_captime.strftime('%Y%m%d/%H%M%S.%f')
                    rkey = 'raw/{}/{}'.format(camid, dtstamp)

                    rds.set(rkey, jpg.tostring())
            sleep(.05)
    except Exception as e:
        log.critical('Critical failure in imgsave')
        log.critical(e)

