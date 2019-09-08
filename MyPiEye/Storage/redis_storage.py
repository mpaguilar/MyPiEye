from datetime import datetime, timedelta
from os import environ
import logging
from functools import partial

from io import BytesIO

import redis

from MyPiEye.CLI import get_config_value

log = logging.getLogger()

class RedisStorage(object):
    def __init__(self, global_config):

        self.cfg = partial(get_config_value, global_config, 'redis')
        self.host = self.cfg('host', 'REDIS_HOST')
        self.port = self.cfg('post', 'REDIS_PORT')
        self.db = self.cfg('db', 'REDIS_DB')
        self.image_prefix = self.cfg('image_prefix', 'REDIS_IMG_PREFIX')

    def check(self):
        return True

    def configure(self):
        return True