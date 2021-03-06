import unittest
import logging

from unittest.mock import Mock

from MyPiEye.configure_app import ConfigureApp
from MyPiEye.CLI import load_config


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

        config = load_config(Mock(), Mock(), 'D:\\Data\\projects\\python\\tmp\\mypieye.ini')
        config['credential_folder'] = 'D:\\Data\\projects\\python\\tmp'

        ca = ConfigureApp(config)
        ret = ca.prepare_gdrive('google_auth.json')
        self.assertTrue(ret)
