import unittest
from unittest import mock

from main_app import MainApp, UsbCamera
from MyPiEye.motion_detect import MotionDetect

config = {'gdrive': {'folder_name': 'mypieye',
                     'client_id': '',
                     'client_secret': ''},
          'minsizes': {'minsize': '1500', 'min_width': '100', 'min_height': '50'},
          'ignore': {'trees': '(0, 0, 1980, 500)', 'lbush': '(648, 537, 448, 221)',
                     'rbush3': '(1601, 476, 188, 92)', 'rbush1': '(1715, 594, 177, 122)',
                     'rbush2': '(1716, 457, 75, 77)'}, 'savedir': 'd:/tmp/mypieye', 'credential_folder': '.',
          'resolution': '720p', 'camera': '0', 'loglevel': 'DEBUG', 'logfile': '', 'color': 'True'}


class MainAppTests(unittest.TestCase):

    def test_init(self):
        app = MainApp(config)

        self.assertIsNotNone(app)
        self.assertIsInstance(app.camera, UsbCamera)
        self.assertDictEqual(app.config, config)
        self.assertIsInstance(app.motiondetect, MotionDetect)

    def test_start(self):
        app = MainApp(config)

        app.camera = mock.Mock()
        app.camera.init_camera = mock.Mock(return_value=True)
        app.camera.close_camera = mock.Mock(return_value=None)

        app.executor = mock.Mock()
        app.executor.shutdown = mock.Mock(return_value=None)

        app.watch_for_motions = mock.Mock(return_value=True)

        # everything works as expected
        ret = app.start()
        self.assertTrue(ret)

        # camera initialization fails
        app.camera.init_camera = mock.Mock(return_value=False)
        ret = app.start()
        self.assertFalse(ret)
