import unittest
from unittest.mock import patch
import CLI


class CliTests(unittest.TestCase):
    def test_load_config(self):
        with self.assertRaises(FileNotFoundError):
            CLI.load_config(None, None, 'bogus.ini')

        ret = CLI.load_config(None, None, '../PiEye/pieye.ini')
        self.assertIsNotNone(ret)
        self.assertIsInstance(ret, dict)
