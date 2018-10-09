from .file_upload import FileUpload
from .google_drive import GDrive
from .local import local_save


def save_files(savedir, subdir, box_name, nobox_name):
    """
    Saves files to Storage
    :param savedir: the base directory
    :param box_name: the path to the temporary annotated file
    :param nobox_name: the path to the temporary clean file
    :param subdir: the subdirectory within the base directory
    :return: None
    """

    local_save(savedir, box_name, nobox_name, subdir)

