import unittest
import logging
from os import remove, environ

from Storage.google_drive import GDriveAuth, GDriveStorage

# no, these don't work. You'll have to generate your own.
CLIENT_ID = '990858881415-u53d5skorvuuq4hqjfj5pvq80d059744.apps.googleusercontent.com'
CLIENT_SECRET = '-9q0wn7j8x7IGrCRcwuzQY0g'
GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file'

logging.basicConfig(level=logging.DEBUG)


class GDriveTests(unittest.TestCase):

    _folder_id = None

    @classmethod
    def setUpClass(cls):
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        ret = GDriveStorage.create_folder(gauth, 'mypieye_test_upload', parent_id='root')

        cls._folder_id = ret

    @classmethod
    def tearDownClass(cls):
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        ret = GDriveStorage.delete_folder(gauth, cls._folder_id)

        assert ret

    def test_validated_auth(self):
        # test validated app
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        self.assertIsNotNone(gauth)
        self.assertIsNotNone(gauth.access_token)
        self.assertIsNotNone(gauth.refresh_token)
        self.assertIsNotNone(gauth.token_expires)

    def test_upload(self):
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        gstorage = GDriveStorage(gauth, 'mypieye_test_upload')

        # upload the file
        ret = gstorage.upload_file('testsub', 'data/test_image.jpg')
        self.assertIsNotNone(ret)


class GDriveFolderTests(unittest.TestCase):
    """
    Before running, be sure you want changes made to your gdrive.
    Will attempt to create a folder named 'mypieye_test' off of the root. It should not exist.
    """

    @unittest.skipUnless(environ.get('INTEGRATION', False), 'Integration test')
    def test_auth(self):
        """
        IMPORTANT: this will prompt at the command line!
        """
        remove('data/test_auth.json')

        # test validation
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        self.assertIsNotNone(gauth)
        self.assertIsNotNone(gauth.access_token)
        self.assertIsNotNone(gauth.refresh_token)
        self.assertIsNotNone(gauth.token_expires)

    # @unittest.skipUnless(environ.get('INTEGRATION', False), 'Integration test')
    def test_folder_creation(self):
        """
        Attempts to create main folder, subfolder, and then delete them.
        :return:
        """

        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')

        # create main folder
        ret = GDriveStorage.create_folder(gauth, 'mypieye_test', 'root')
        self.assertIsNotNone(ret)
        folder_id = ret

        gstorage = GDriveStorage(gauth, 'mypieye_test')

        # find main folder
        ret = gstorage.main_folder()
        self.assertIsNotNone(ret)

        # did we find the folder we created?
        self.assertEqual(folder_id, ret)

        # create a subfolder
        ret = gstorage.create_subfolder('subfolder_test')
        self.assertIsNotNone(ret)

        subid = ret

        # find the subfolder
        ret = GDriveStorage.find_folders(gauth, parent_id=folder_id, folder_name='subfolder_test')
        self.assertIsNotNone(ret)
        self.assertEqual(1, len(ret['files']))

        # delete the subfolder
        ret = GDriveStorage.delete_folder(gauth, folder_id=subid)
        self.assertTrue(ret)

        # delete main folder
        ret = GDriveStorage.delete_folder(gauth, folder_id=folder_id)
        self.assertTrue(ret)
