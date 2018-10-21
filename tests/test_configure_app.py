import unittest
import logging

logging.basicConfig(level=logging.DEBUG)

from MyPiEye.configure_app import ConfigureApp


class CongfigureAppTests(unittest.TestCase):

    def test_prepare_camera(self):
        config = {
            'camera': 0,
            'resolution': '720p'
        }

        configapp = ConfigureApp(config)
        ret = configapp.prepare_camera()
        self.assertTrue(ret)

    def test_prepare_local_storage(self):
        config = {
            'savedir': 'data/fakesavedir'
        }

        configapp = ConfigureApp(config)
        ret = configapp.prepare_local_storage()
        self.assertTrue(ret)

    def test_prepare_working_directories(self):
        config = {
            'workdir': 'data/fakeworkdir'
        }

        ca = ConfigureApp(config)
        ret = ca.prepare_working_directories()
        self.assertTrue(ret)

    def test_prepare_gdrive(self):

        config = {
            'credential_folder': 'data',
            'gdrive':
                {
                    'folder_name': 'mypieye_test_config',
                    'client_id': '',
                    'client_secret': ''
                }
        }

        ca = ConfigureApp(config)
        ret = ca.prepare_gdrive('test_auth.json')
        self.assertTrue(ret)
