from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.session.combined_coverage import combined_coverage
from pycrunch.session.file_map import test_map
import logging

logger = logging.getLogger(__name__)


class TestState:
    def __init__(self, discovered_test, execution_result, pinned):
        self.discovered_test = discovered_test
        self.pinned = pinned
        self.execution_result = execution_result

class AllTests:
    def __init__(self):
        # fqn -> TestState
        self.tests = dict()

    def test_discovered(self, fqn, discovered_test, is_pinned):
        # todo preserve state
        self.tests[fqn] = TestState(discovered_test, ExecutionResult(), is_pinned)
        combined_coverage.test_did_removed(fqn)

    def test_will_run(self, fqn):
        test_to_be_run = self.tests.get(fqn, None)
        test_to_be_run.execution_result.run_did_queued()

    def test_did_run(self, fqn, test_run):
        test_to_be_run = self.tests.get(fqn, None)
        #  TestState
        test_to_be_run.execution_result = test_run.execution_result

    def pin_test(self, fqn):
        test_to_pin = self.tests.get(fqn, None)
        test_to_pin.pinned = True

    def unpin_test(self, fqn):
        test_to_unpin = self.tests.get(fqn, None)
        test_to_unpin.pinned = False

    def legacy_aggregated_statuses(self):
        # todo rename to status for consistency
        return {fqn: dict(state=test_run_short_info.execution_result.status) for fqn, test_run_short_info in self.tests.items()}


    def collect_by_fqn(self, fqns):
        result = list()
        logger.info(f'collecting {len(fqns)} tests for run')
        for fqn in fqns:

            current_test = self.tests[fqn]
            self.log_test_details(current_test)
            result.append(current_test)

        return result

    def log_test_details(self, current_test):
        logger.debug(f'---')
        logger.debug(f'current_test filename is {current_test.discovered_test.filename}')
        logger.debug(f'current_test fqn is {current_test.discovered_test.fqn}')
        logger.debug(f'current_test module is {current_test.discovered_test.module}')
        logger.debug(f'---')

    def get_pinned_tests(self):
        result = set()
        for test in self.tests.values():
            if test.pinned:
                result.add(test.discovered_test.fqn)
        return result

    def discard_tests_not_in_map(self):
        for fqn in list(self.tests):
            test = self.tests[fqn]
            if not test_map.test_exist(test.discovered_test.filename, fqn):
                print(f'test no longer in file_map {fqn} - Removed')
                del self.tests[fqn]
                combined_coverage.test_did_removed(fqn)

all_tests = AllTests()