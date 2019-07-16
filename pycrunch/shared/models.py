from collections import namedtuple

from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.session.combined_coverage import combined_coverage
from pycrunch.session.file_map import test_map

TestMetadata = namedtuple('TestMetadata', ['filename', 'name', 'module', 'fqn', 'state'])

class TestState:
    def __init__(self, discovered_test, execution_result):
        self.discovered_test = discovered_test
        self.execution_result = execution_result

class AllTests:
    def __init__(self):
        # fqn -> TestState
        self.tests = dict()

    def test_discovered(self, fqn, discovered_test):
        # todo preserve state
        self.tests[fqn] = TestState(discovered_test, ExecutionResult())

    def test_will_run(self, fqn):
        test_to_be_run = self.tests.get(fqn, None)
        test_to_be_run.execution_result.run_did_queued()

    def test_did_run(self, fqn, test_run):
        test_to_be_run = self.tests.get(fqn, None)
        #  TestState
        test_to_be_run.execution_result = test_run.execution_result

    def legacy_aggregated_statuses(self):
        # todo rename to status for consistency
        return {fqn: dict(state=test_run_short_info.execution_result.status) for fqn, test_run_short_info in self.tests.items()}


    def collect_by_fqn(self, fqns):
        result = list()
        for fqn in fqns:
            result.append(self.tests[fqn])

        return result

    def discard_tests_not_in_map(self):
        for fqn in list(self.tests):
            test = self.tests[fqn]
            if not test_map.test_exist(test.discovered_test.filename, fqn):
                print(f'test no longer in file_map {fqn} - Removed')
                del self.tests[fqn]
                combined_coverage.test_did_removed(fqn)

all_tests = AllTests()