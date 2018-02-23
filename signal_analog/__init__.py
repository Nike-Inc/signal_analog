# -*- coding: utf-8 -*-

"""Top-level package for Signal Analog."""

import logging.config
import pkg_resources
import yaml

__author__ = """Fernando Freire"""
__email__ = 'Lst-nike.plus.platform.sharedinfrastructure@nike.com'
__version__ = '0.20.0'

logging_config = pkg_resources.resource_string(
    __name__, 'logging.yaml').decode('utf-8')

logging.config.dictConfig(yaml.load(logging_config))

logger = logging.getLogger()
