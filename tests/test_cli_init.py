import unittest

from unittest.mock import patch
from unittest import mock

import CLI


class CliTests(unittest.TestCase):
    def test_load_config(self):
        with self.assertRaises(FileNotFoundError):
            CLI.load_config(None, None, 'bogus.ini')

        fake_ctx = mock.Mock()
        fake_ctx.params = {'loglevel': 'CRITICAL', 'logfile': None, 'color': False}

        ret = CLI.load_config(fake_ctx, None, 'data/fake.ini')

        goodret = {'gdrive': {'folder_name': 'mypieye',
                              'client_id': '',
                              'client_secret': ''},
                   'minsizes': {'minsize': '1500', 'min_width': '100', 'min_height': '50'},
                   'ignore': {'trees': '(0, 0, 1980, 500)', 'lbush': '(648, 537, 448, 221)',
                              'rbush3': '(1601, 476, 188, 92)', 'rbush1': '(1715, 594, 177, 122)',
                              'rbush2': '(1716, 457, 75, 77)'}, 'savedir': 'd:/tmp/mypieye', 'credential_folder': '.',
                   'resolution': '720p', 'camera': '0', 'loglevel': 'DEBUG', 'logfile': '', 'color': 'True'}

        self.assertIsNotNone(ret)
        self.assertIsInstance(ret, dict)

        ret['gdrive']['client_id'] = ''
        ret['gdrive']['client_secret'] = ''

        self.assertDictEqual(goodret, ret)
