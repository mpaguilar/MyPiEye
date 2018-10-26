from shutil import copyfile
from os.path import basename, exists
from os import makedirs
import logging

import multiprocessing

from MyPiEye.motion_detect import ImageCapture

log = multiprocessing.get_logger()


def local_save(savedir, img_capture: ImageCapture):
    """
    Copies the files to the local filesystem.
    If the subdirectories don't exist, they will be created.

    :param savedir: The local base directory to save files
    :param img_capture: ``ImageCapture`` object

    :return: ImageCapture object
    """

    if not exists(savedir):
        raise EnvironmentError('savedir {} does not exist'.format(savedir))

    savedir = savedir + '/' + img_capture.subdir

    if not exists(savedir):
        makedirs(savedir)

    if not exists(savedir + '/box'):
        makedirs(savedir + '/box')

    if not exists(savedir + '/nobox'):
        makedirs(savedir + '/nobox')

    log.debug('Saving files to {}'.format(savedir))

    box_name = img_capture.full_fname
    nobox_name = img_capture.clean_fname

    box_path = '{}/box/{}'.format(savedir, basename(box_name))
    nobox_path = '{}/nobox/{}'.format(savedir, basename(nobox_name))

    log.debug('Copying {}'.format(box_name))
    copyfile('{}'.format(box_name), box_path)

    log.debug('Copying {}'.format(nobox_name))
    copyfile('{}'.format(nobox_name), nobox_path)

    return img_capture
