import logging
log = logging.getLogger(__name__)

class Startup(object):

    def __init__(self, config):
        """
        The workhorse of the program.

        :param config: a dict of consolidated options (defaults, ini, cmdline)
        """

        self.config = config
