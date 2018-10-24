import logging
import unittest
from unittest.mock import Mock

from MyPiEye.Storage import S3Storage
from MyPiEye.CLI import load_config

logging.basicConfig(level=logging.INFO)

class S3Tests(unittest.TestCase):

    def test_upload(self):
        config = load_config(Mock(), Mock(), 'D:\\Data\\projects\\python\\tmp\\mypieye.ini')
        config['credential_folder'] = 'D:\\Data\\projects\\python\\tmp'

        s3 = S3Storage(config)

        ret = s3.upload('test/this', 'data/test_image.jpg')
        self.assertTrue(ret)


