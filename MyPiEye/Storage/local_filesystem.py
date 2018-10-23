from shutil import copyfile
from os.path import basename, exists
from os import makedirs
import logging

log = logging.getLogger(__name__)


def local_save(savedir, box_name, nobox_name, subdirectory):
    """
    Copies the files to the local filesystem.
    If the subdirectories don't exist, they will be created.

    :param savedir: The local base directory to save files
    :param box_name: the filename of the image with boxes
    :param nobox_name: the filename of a clean image
    :param subdirectory: the subdirectory to store them in

    :return: tuple of resolved filenames. Raises if the base directory doesn't exist.
    """

    if not exists(savedir):
        raise EnvironmentError('savedir {} does not exist'.format(savedir))

    savedir = savedir + '/' + subdirectory

    if not exists(savedir):
        makedirs(savedir)

    if not exists(savedir + '/box'):
        makedirs(savedir + '/box')

    if not exists(savedir + '/nobox'):
        makedirs(savedir + '/nobox')

    log.debug('Saving files to {}'.format(savedir))

    box_path = '{}/box/{}'.format(savedir, basename(box_name))
    nobox_path = '{}/nobox/{}'.format(savedir, basename(nobox_name))

    log.debug('Copying {}'.format(box_name))
    copyfile('{}'.format(box_name), box_path)

    log.debug('Copying {}'.format(nobox_name))
    copyfile('{}'.format(nobox_name), nobox_path)

    return box_path, nobox_path
