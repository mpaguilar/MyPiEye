from os.path import exists
from datetime import datetime

import cv2
import numpy as np

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

    def make_gray(self, img):
        """
        Converts image to grayscale.

        :param img: CV image
        :return: gray CV image
        """
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        g = cv2.GaussianBlur(g, (21, 21), 0)
        return g

    def annotate_image(self, img, dtstamp, movements):
        """
        Adds timestamp, motion boxes

        :param img: CV image
        :param dtstamp: timestamp
        :param movements: list of motion boxes
        :return: a copy of the CV image, annotated
        """
        copied = img.copy()
        for b in movements:
            (x, y, w, h) = b['rect']
            cv2.rectangle(copied, (x, y), (x + w, y + h), (255, 255, 255), 2)

        cv2.putText(copied, dtstamp + ' UTC',
                    (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    .7, (255, 255, 255), 2
                    )
        return copied

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

        gray1 = self.make_gray(img1)
        gray2 = self.make_gray(img2)

        frame_diff = cv2.absdiff(gray1, gray2)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        thresh = thresh[1]

        thresh = cv2.dilate(thresh, None, iterations=2)
        contours = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

        if 0 == len(contours):
            return (False, [])

        for c in contours:
            size = cv2.contourArea(c)
            rect = cv2.boundingRect(c)

            if self.ignore(rect, size):
                continue

            movements.append({
                'rect': rect,
                'size': size
            })

        if 0 == len(movements):
            return False, []

        return True, movements



    def compare_files(self, file1, file2):
        """
        Compares two files.

        :return: the result of compare_images
        """

        if not exists(file1):
            print("Error opening {}".format(file1))
            return self.false_return

        if not exists(file2):
            print("Error opening {}".format(file2))
            return self.false_return

        img1 = cv2.imread(file1)
        img2 = cv2.imread(file2)

        return self.compare_images(img1, img2)

    def convert_pil(self, img):
        """
        Converts a PIL image (from webcam stream) to CV image

        :param img: PIL image
        :return: CV image
        """
        if not img:
            log.error("Bad image")
            return []

        img = img.convert('RGB')
        img = np.array(img)
        cvimg = img[:, :, ::-1].copy()
        return cvimg

    def motions(self, current_img):
        """
        Compares passed in image with stored previous image.
        If previous image does not exist, then a negative result (no changes) is returned.

        :param current_img: CV image
        :return: a tuple containing the result, and if True,
            a datetime when the image was processed, a filename for the current image,
            a filename for the annotated image, and a list of motions detected as boxes.

        """

        ret = (False, '', '', '', '')

        dtnow = datetime.utcnow()
        ymd = dtnow.strftime('%y%m%d')
        hms = dtnow.strftime('%H%M%S.%f')
        dtstamp = dtnow.strftime('%y/%m/%d %H:%M:%S.%f')

        if 0 == len(current_img):
            log.error('Invalid image: {}'.format(current_img))
            # if the resolution changes, we'll blow up
            self.prev_filename = None

            return self.false_return

        # temporary files have hms filename
        self.current_filename = '{}/{}.jpg'.format(self.workdir, hms)
        # cv2.imwrite(self.current_filename, current_img)

        if self.prev_image is not None:

            motion, movements = self.compare_images(
                self.prev_image, current_img)

            if motion:
                # motion files have ymd.hms filename
                log.debug("Motion detected in {} places".format(len(movements)))
                box_fname = '{}/{}.{}.box.jpg'.format(self.workdir, ymd, hms)
                orig_fname = '{}/{}.{}.jpg'.format(self.workdir, ymd, hms)

                with_box = self.annotate_image(current_img, dtstamp, movements)

                cv2.imwrite(box_fname, with_box)
                cv2.imwrite(orig_fname, current_img)

                ret = (True, dtnow, orig_fname, box_fname, movements)

            # self.del_filename = self.prev_filename

        self.prev_image = current_img.copy()

        return ret

    def set_ignore(self, set_minsize, set_ignore_boxes, min_height, min_width):
        """
        Sets minimums and ignore boxes

        :param set_minsize: the smallest box allowed
        :param set_ignore_boxes: a list of regions to ignore
        :param min_height: the smallest height allowed
        :param min_width: the smallest width allowed
        :return:
        """

        self.minsize = set_minsize
        self.min_height = min_height
        self.min_width = min_width
        self.ignore_boxes = set_ignore_boxes

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

            # print(' - ignore: {}'.format(igbox))
            # size: 2950.0,  x: 1448, y: 0, w: 65, h: 98
            (ix, iy, iw, ih) = igbox
            if ix <= x and (ix + iw) >= (x + w) and \
                    iy <= y and (iy + ih) >= (y + h):
                return True

        return False
