import unittest
import logging
from os import remove, environ

from Storage.google_drive import GDriveAuth, GDriveStorage

CLIENT_ID = '990858881415-u53d5skorvuuq4hqjfj5pvq80d059744.apps.googleusercontent.com'
CLIENT_SECRET = '-9q0wn7j8x7IGrCRcwuzQY0g'
GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file'

logging.basicConfig(level=logging.DEBUG)


class GDriveTests(unittest.TestCase):
    """
    Before running, be sure you want changes made to your gdrive.
    Will attempt to create a folder named 'mypieye_test' off of the root. It should not exist.
    Expects a folder named `mypieye_test` off of the root.
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

    def test_validated_auth(self):
        # test validated app
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        self.assertIsNotNone(gauth)
        self.assertIsNotNone(gauth.access_token)
        self.assertIsNotNone(gauth.refresh_token)
        self.assertIsNotNone(gauth.token_expires)

    @unittest.skipUnless(environ.get('INTEGRATION', False), 'Integration test')
    def test_folder_creation(self):
        """
        Attempts to create main folder, subfolder, and then delete them.
        :return:
        """

        # create it
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        gstorage = GDriveStorage(gauth, 'mypieye_test')

        ret = gstorage.create_main_folder()
        self.assertIsNotNone(ret)
        folder_id = ret['id']

        # find it
        ret = gstorage.find_folder()
        self.assertIsNotNone(ret)
        self.assertEqual(1, len(ret['files']))

        # did we find the folder we created?
        self.assertEqual(folder_id, ret['files'][0]['id'])

        # create a subfolder
        ret = gstorage.create_subfolder('subfolder_test')
        self.assertIsNotNone(ret)

        subid = ret['id']

        # find the subfolder
        ret = gstorage.find_folder(parent_id=folder_id, name='subfolder_test')
        self.assertIsNotNone(ret)
        self.assertEqual(1, len(ret['files']))

        # delete the subfolder
        ret = gstorage.delete_folder(folder_id=subid)
        self.assertTrue(ret)

        # delete main folder
        ret = gstorage.delete_folder()
        self.assertTrue(ret)

    def test_upload(self):
        gauth = GDriveAuth.init_gauth(CLIENT_ID, CLIENT_SECRET, 'data/test_auth.json')
        gstorage = GDriveStorage(gauth, 'mypieye_test')

        # find the main folder
        ret = gstorage.find_folder('mypieye_test')
        self.assertEqual(1, len(ret['files']))

        # create the main folder
        ret = gstorage.create_main_folder()
        self.assertIsNotNone(ret)
        folder_id = ret['id']

        # upload the file
        gstorage.upload_file('testsub', 'data/test_image.jpg')

        # delete main folder
        # ret = gstorage.delete_folder(folder_id)
        # self.assertTrue(ret)







