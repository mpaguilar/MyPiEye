import unittest
from unittest.mock import patch
import CLI

from click.testing import CliRunner

import pieye


class CliTests(unittest.TestCase):
    def test_load_config(self):
        with self.assertRaises(FileNotFoundError):
            CLI.load_config(None, None, 'bogus.ini')

        ret = CLI.load_config(None, None, '../PiEye/pieye.ini')
        self.assertIsNotNone(ret)
        self.assertIsInstance(ret, dict)

    def test_bad_opts(self):
        runner = CliRunner()

        ret = runner.invoke(
            pieye.motion,
            ['--loglevel', 'bogus'],
            catch_exceptions=False
        )

        self.assertEqual(2, ret.exit_code)


