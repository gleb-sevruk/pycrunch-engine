import sys
from pathlib import Path
from pprint import pprint

import yaml

from pycrunch.plugins.pytest_support.hot_reload import unload_candidates
import logging.config
import logging

logger = logging.getLogger(__name__)


# http://forums.cgsociety.org/t/proper-way-of-reloading-a-python-module-with-new-code-without-having-to-restart-maya/1648174/8

class ModuleCleanup():
    def __init__(self):
        self.modules_before = []

    def __enter__(self):
        self.modules_before = set(sys.modules)
        # self.apply_log_config()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        modules_after = set(sys.modules)
        difference = set(modules_after).difference(self.modules_before)
        modules_for_unload = unload_candidates(difference)
        # pprint(modules_for_unload)
        for m in modules_for_unload:
        # wont work witth django without check?! find out why?
            if m in sys.modules:
                del sys.modules[m]

    def apply_log_config(self):
        parent = Path(__file__).parent.parent.parent
        print(parent)
        configuration_yaml_ = parent.joinpath('log_configuration.yaml')
        print(configuration_yaml_)
        with open(configuration_yaml_, 'r') as f:
            logger.info('aaa')
            logging.config.dictConfig(yaml.safe_load(f.read()))
            logger.info('bbb')
