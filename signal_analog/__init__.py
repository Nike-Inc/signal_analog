# -*- coding: utf-8 -*-

"""Top-level package for Signal Analog."""

import logging.config
import pkg_resources
import yaml
import os

__author__ = """Fernando Freire"""
__email__ = 'Lst-nike.plus.platform.sharedinfrastructure@nike.com'
__version__ = '2.7.2.dev0'

logging_config = pkg_resources.resource_string(
    __name__, 'logging.yaml').decode('utf-8')

# Fix for yaml loader according to https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
logging.config.dictConfig(yaml.load(logging_config, Loader=yaml.SafeLoader))

logger = logging.getLogger()


def debug(msg):
    if os.environ.get('LOG_LEVEL', '').lower() == 'debug':
        logger.debug(msg)
