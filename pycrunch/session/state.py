import logging
from pathlib import Path

from pycrunch.api.serializers import serialize_test_set_state
from pycrunch.api.shared import pipe
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.session import config
from pycrunch.session.diagnostics import diagnostic_engine
from pycrunch.shared.models import all_tests

logger = logging.getLogger(__name__)


                                                                                                                                                        
class EngineState:
    def __init__(self):
        # self.all_tests = dict()
        folder_auto = str(Path('.').absolute())
        logger.info(f'folder is: {folder_auto}')
        self.folder = folder_auto
        self.all_tests = all_tests
        self.runtime_configuration_ready = False
        pass

    def will_start_test_discovery(self):
        from pycrunch.discovery.simple import SimpleTestDiscovery
        self.prepare_runtime_configuration_if_necessary()

        discovery_engine = SimpleTestDiscovery()
        test_set = discovery_engine.find_tests_in_folder(self.folder)
        engine.test_discovery_will_become_available(test_set)

        pass

    def will_start_diagnostics_collection(self):
        logger.info('will_start_diagnostics_collection')
        pipe.push(event_type='diagnostics_did_become_available', engine=config.runtime_engine, **diagnostic_engine.summary())
        logger.info('diagnostics_did_become_available')

    def test_discovery_will_become_available(self, test_set):
        """
        :type test_set: pycrunch.discovery.simple.TestSet
        """
        for discovered_test in test_set.tests:
            self.all_tests.test_discovered(discovered_test.fqn, discovered_test)

        self.all_tests.discard_tests_not_in_map()
        self.notify_clients_about_tests_change()
        logger.info('discovery_did_become_available')

    def notify_clients_about_tests_change(self):
        logger.info('notify_clients_about_tests_change')
        pipe.push(event_type='discovery_did_become_available', **serialize_test_set_state(self.all_tests.tests), folder=self.folder)

    def tests_will_run(self, tests):
        logger.info('tests_will_run')

        for test in tests:
            self.all_tests.test_will_run(test.discovered_test.fqn)

        self.notify_clients_about_tests_change()

    def tests_did_run(self, results):
        for k, v in results.items():
            self.all_tests.test_did_run(k, v)

        self.notify_clients_about_tests_change()

    def prepare_runtime_configuration_if_necessary(self):
        if not self.runtime_configuration_ready:
            self.runtime_configuration_ready = True
            config.load_runtime_configuration()


engine = EngineState()



