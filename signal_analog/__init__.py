# -*- coding: utf-8 -*-

"""Top-level package for Signal Analog."""

import logging.config
import pkg_resources
import yaml

# These two lines disable debugging at httplib level
# (requests->urllib3->http.client)
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 0


__author__ = """Fernando Freire"""
__email__ = 'Lst-nike.plus.platform.sharedinfrastructure@nike.com'
__version__ = '0.20.0'

logging_config = pkg_resources.resource_string(
    __name__, 'logging.yaml').decode('utf-8')

logging.config.dictConfig(yaml.load(logging_config))

logger = logging.getLogger()
