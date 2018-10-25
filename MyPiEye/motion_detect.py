from os.path import exists
from datetime import datetime

import cv2

import logging

log = logging.getLogger(__name__)


class MotionDetect:
    """
    Interface to OpenCV

    """

    def __init__(self, workdir, minsize, ignore_boxes):
        """
        Constructor

        :param workdir: where files will be copied for other modules
        :param minsize: the smallest box size
        :param ignore_boxes: a list of boxes to ignore
        """

        self.workdir = workdir
        self.minsize = minsize
        self.min_width = 0
        self.min_height = 0
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

        if 0 == len(contours):
            return False, []

        # we may not want some of these to count
        for size, rect in contours:

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

        when motion is detected, returns a tuple containing a datetime and a list of motions detected as boxes.

        :param current_img: CV image
        :return: None if no motion

        """

        ret = None

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
                ret = (dtnow, movements)
            else:
                ret = None

        self.prev_image = current_img.copy()

        return ret

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

        ret = []
        for c in contours:
            # get measurements we can use
            size = cv2.contourArea(c)
            rect = cv2.boundingRect(c)
            ret.append((size, rect))

        return ret

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
            cv2.rectangle(copied, (x, y), (x + w, y + h), (255, 255, 255), 2)

        return copied

    @staticmethod
    def add_timestamp(cv_image, dtstamp):
        """
        Adds a timestamp to the image.

        :param cv_image: The image to copy and modify
        :param dtstamp: time as formatted string.
        :return:
        """
        copied = cv_image.copy()

        cv2.putText(copied, dtstamp,
                    (20, 20),  # start location
                    cv2.FONT_HERSHEY_SIMPLEX,
                    .7,  # font scale?
                    (255, 255, 255), 2  # look these up again
                    )

        return copied
