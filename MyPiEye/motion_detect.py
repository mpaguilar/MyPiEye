from datetime import datetime
from os.path import exists, abspath
from os import remove
from ast import literal_eval
import logging

from dateutil import tz

import cv2

log = logging.getLogger(__name__)


class ImageCapture(object):

    def __init__(self, config):

        self.tz = config.get('timezone', None)

        self.cam_id = None

        self.capture_dt = None

        # images, ie numpy arrays
        self.clean_image = None
        self.ts_image = None
        self.full_image = None

        # filenames
        self.clean_fname = None
        self.ts_fname = None
        self.full_fname = None

        # list of co-ordinate lists
        self.motions = None

    def __del__(self):

        log.info('Removing temp files')

        if self.clean_fname is not None and exists(self.clean_fname):
            log.debug('Removing {}'.format(self.clean_fname))
            remove(self.clean_fname)

        if self.ts_fname is not None and exists(self.ts_fname):
            log.debug('Removing {}'.format(self.ts_fname))
            remove(self.ts_fname)

        if self.full_fname is not None and exists(self.full_fname):
            log.debug('Removing {}'.format(self.full_fname))
            remove(self.full_fname)

    @property
    def subdir(self):
        return self.capture_dt.strftime('%y%m%d')

    @property
    def base_filename(self):
        """
        Builds filename from properties. Does not include extension.

        :return:
        """
        ymd = self.capture_dt.strftime('%y%m%d')
        hms = self.capture_dt.strftime('%H%M%S.%f')

        return '{}.{}'.format(ymd, hms)

    @property
    def timestamp_utc(self):
        """
        Capture timestamp, as string

        :return:
        """

        return self.capture_dt.strftime('%y/%m/%d %H:%M:%S.%f')

    @property
    def timestamp_local(self):
        """
        Capture timestamp, converted to whatever is specified in config.

        :return:
        """

        if self.tz is None:
            return ''

        from_tz = tz.gettz('UTC')
        local_tz = tz.gettz(self.tz)

        local = self.capture_dt.replace(tzinfo=from_tz)
        local_dt = local.astimezone(local_tz)

        return local_dt.strftime('%y/%m/%d %H:%M:%S.%f')


class MotionDetect:
    """
    Interface to OpenCV

    """

    def __init__(self, config):
        """
        Constructor

        :param workdir: where files will be copied for other modules
        :param minsize: the smallest box size
        :param ignore_boxes: a list of boxes to ignore
        """

        self.config = config

        self.workdir = abspath(config['workdir'])

        minsizes = config.get('minsizes', {})

        self.minsize = minsizes.get('minsize', 0)
        # this is read as a string from the config
        if isinstance(self.minsize, str):
            self.minsize = literal_eval(self.minsize)

        self.min_width = literal_eval(minsizes.get('min_width', 0))
        self.min_height = literal_eval(minsizes.get('min_height', 0))

        ignore_dict = self.config.get('ignore', {})
        ignore_boxes = []

        for _, v in ignore_dict.items():
            val = literal_eval(v)
            ignore_boxes.append(val)

        self.ignore_boxes = ignore_boxes

        self.prev_filename = None
        self.current_filename = None
        self.del_filename = None

        self.prev_image = None

        self.false_return = (False, None, None, None)

    def compare_images(self, img1, img2):
        """
        Compares two CV images, looking for changes. If the box doesn't meet mininum
        threshholds, or is ignored, it will not be included in the results. If everything
        is ignored, no changes will be reported.

        :param img1: the previous image
        :param img2: the current image
        :return: Tuple with result, and changes if any
        """
        movements = []

        contours = MotionDetect.find_contours(img1, img2)

        # we may not want some of these to count
        for size, rect in list(contours):

            # is this one being ignored?
            if self.ignore(rect, size):
                continue

            # add it to the list
            movements.append({
                'rect': rect,
                'size': size
            })

        if 0 == len(movements):
            return False, []

        return True, movements

    def ignore(self, movement, size):
        """
        Checks movement box against list of ignored boxes, and minimum size, width, height

        :param movement:
        :param size:
        :return: True if ignored.
        """

        if self.minsize != 0 and size < self.minsize:
            return True

        x, y, w, h = movement

        if w <= self.min_width:
            return True

        if h <= self.min_height:
            return True

        for igbox in self.ignore_boxes:
            (ix, iy, iw, ih) = igbox
            if ix <= x and (ix + iw) >= (x + w) and \
                    iy <= y and (iy + ih) >= (y + h):
                return True

        return False

    def motions(self, current_img):
        """
        Compares passed in image with stored previous image.
        If previous image does not exist, then a negative result (no changes) is returned.

        when motion is detected, returns an ImageCapture object with capture_dt and motions set.

        :param current_img: CV image
        :return: None if no motion, ImageCapture if there is.

        """

        ret_img = None

        dtnow = datetime.utcnow()

        if 0 == len(current_img):
            log.error('Invalid image: {}'.format(current_img))
            # if the resolution changes, we'll blow up
            self.prev_filename = None

            return None

        if self.prev_image is not None:

            motion, movements = self.compare_images(
                self.prev_image, current_img)

            if motion:
                ret_img = ImageCapture(self.config)  # (dtnow, movements)
                ret_img.capture_dt = dtnow
                ret_img.motions = movements
            else:
                ret_img = None

        self.prev_image = current_img.copy()

        return ret_img

    @staticmethod
    def find_contours(img1, img2):
        """
        Relies on OpenCV to do the hard work.

        :param img1: cv image
        :param img2: cv image
        :return: A list of (size, rect) tuples.
        """
        # CV voodoo happens here

        # color doesn't help, get rid of it
        gray1 = MotionDetect.make_gray(img1)
        gray2 = MotionDetect.make_gray(img2)

        # finds differences as blobs
        frame_diff = cv2.absdiff(gray1, gray2)
        # refines those blobs to make them blocky
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        # returns a tuple, we only want the second value
        thresh = thresh[1]

        # make those blocks really stand out.
        thresh = cv2.dilate(thresh, None, iterations=2)

        # these are ulitmately what we want
        contours = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

        ret_ = []
        for c in contours:
            # get measurements we can use
            size = cv2.contourArea(c)
            rect = cv2.boundingRect(c)
            yield (size, rect)

    @staticmethod
    def make_gray(cv_image):
        """
        Converts image to grayscale.

        :param cv_image: CV image
        :return: gray CV image
        """
        g = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        g = cv2.GaussianBlur(g, (21, 21), 0)
        return g

    @staticmethod
    def save_cv_image(cv_image, filename):
        """
        Write the image as a file.

        :param cv_image:
        :param filename:
        :return:
        """
        cv2.imwrite(filename, cv_image)

    @staticmethod
    def add_motion_boxes(cv_image, movements):
        """
        Adds white boxes where motion was detected

        :param cv_image: CV2 image to copy and modify
        :param movements: a list of movement lists.
        :return: a copy CV2 image with boxes.
        """
        copied = cv_image.copy()
        for b in movements:
            (x, y, w, h) = b['rect']
            cv2.rectangle(copied, (x, y), (x + w, y + h), (192, 192, 192), 1)

        return copied

    @staticmethod
    def add_timestamp(cv_image, dtstamp):
        """
        Adds a timestamp to the image.

        :param cv_image: The image to copy and modify
        :param utc_capture_dt: A UTC datetime
        :return:
        """
        copied = cv_image.copy()

        cv2.putText(copied, dtstamp,
                    (10, 20),  # start location
                    cv2.FONT_HERSHEY_SIMPLEX,
                    .7,  # font scale?
                    (192, 192, 192),  # the color
                    2  # the width of the lines to draw the font
                    )

        return copied
