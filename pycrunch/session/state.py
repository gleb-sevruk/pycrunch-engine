import logging

from pycrunch.api.serializers import serialize_test_set_state
from pycrunch.api.shared import pipe
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.session import config

logger = logging.getLogger(__name__)

class TestState:
    def __init__(self, discovered_test, execution_result):
        self.discovered_test = discovered_test
        self.execution_result = execution_result


class EngineState:
    def __init__(self):
        self.all_tests = dict()
        self.folder = ''
        self.runtime_configuration_ready = False
        pass

    def will_start_test_discovery(self, folder):
        from pycrunch.discovery.simple import SimpleTestDiscovery
        self.prepare_runtime_configuration_if_necessary()

        discovery_engine = SimpleTestDiscovery()
        test_set = discovery_engine.find_tests_in_folder(folder)
        self.folder = folder
        engine.test_discovery_will_become_available(test_set, folder=folder)

        pass

    def test_discovery_will_become_available(self, test_set, folder):
        """
        :type test_set: pycrunch.discovery.simple.TestSet
        """
        for single_test in test_set.tests:
            self.all_tests[single_test.fqn] = TestState(single_test, ExecutionResult())

        self.notify_clients_about_tests_change()
        logger.info('discovery_did_become_available')

    def notify_clients_about_tests_change(self):
        logger.info('notify_clients_about_tests_change')
        pipe.push(event_type='discovery_did_become_available', **serialize_test_set_state(self.all_tests), folder=self.folder)

    def tests_will_run(self, tests):
        logger.info('tests_will_run')

        for test in tests:
            test_to_be_run = self.all_tests.get(test['fqn'], None)
            #  TestState
            test_to_be_run.execution_result.run_did_queued()

        self.notify_clients_about_tests_change()

    def tests_did_run(self, results):
        for k, v in results.items():
            test_to_be_run = self.all_tests.get(k, None)
            #  TestState
            test_to_be_run.execution_result = v.execution_result

        self.notify_clients_about_tests_change()

    def prepare_runtime_configuration_if_necessary(self):
        if not self.runtime_configuration_ready:
            self.runtime_configuration_ready = True
            config.load_runtime_configuration()


engine = EngineState()



