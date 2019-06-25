import logging
import os
import sys
import traceback
from collections import namedtuple
import importlib.util
from pprint import pprint

import coverage
import pytest

from pycrunch.api.serializers import serialize_test_run
from pycrunch.api.shared import timestamp
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner import _abstract_runner, exclusions
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.runner.interception import capture_stdout

logger = logging.getLogger(__name__)

TestMetadata = namedtuple('TestMetadata', ['filename', 'name', 'module', 'fqn', 'state'])

# todo join 2 classes

class PyTestRunner(_abstract_runner.Runner):
    def __init__(self):
        pass

    def run(self, tests):

        results = dict()
        for test_to_run in tests:
            cov = self.start_coverage()
            try:
                with capture_stdout() as get_value:
                    time_start = timestamp()
                    metadata = TestMetadata(**test_to_run)
                    execution_result = self._run_test(metadata)
                    time_end = timestamp()
                    time_elapsed = time_end - time_start
                    cov.stop()
                    fqn = metadata.fqn
                    captured_output = get_value()

                    execution_result.output_did_become_available(captured_output)
                    coverage_for_run = serialize_test_run(cov, fqn, time_elapsed, test_metadata=test_to_run, execution_result=execution_result)
            except Exception as e:
                logger.exception('error during run', exc_info=e)
            results[fqn] = coverage_for_run

        return results

    def start_coverage(self):
        cov = coverage.Coverage(config_file=False, branch=True, omit=exclusions.exclude_list)
        # comment this line to be able to debug
        cov.start()
        return cov

    def _run_test(self, test: TestMetadata) -> ExecutionResult:
        execution_result = ExecutionResult()
        try:
            fqn_test_to_run = test.filename + '::' + test.name
            pprint(fqn_test_to_run)
            plugin = PyTestInterceptionPlugin(tests_to_run=[fqn_test_to_run])
            print('xxx')

            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
            print(os.getpid())
            pprint(dict(passed_tests=plugin.passed_tests))
            pprint(dict(failed_tests=plugin.failed_tests))

            # maybe context manager ?

            print('testing output interception')
            # print(vars(foo))
            if plugin.guess_run_status(test.name):
                execution_result.run_did_succeed()
            else:
                execution_result.run_did_fail()

            # logger.debug('after exec_module')
        except Exception as e:
            etype, value, current_traceback = sys.exc_info()
            execution_result.record_exception(etype=etype, value=value, current_traceback=current_traceback)
            execution_result.run_did_fail()
            last_call = -1
            traceback.print_exception(etype=etype, value=value, tb=current_traceback, limit=last_call, file=sys.stdout)
            # traceback.print_exc(file=sys.stdout)
            # print(str(e))
            logger.exception('Error while executing _run_test', exc_info=e)

        return execution_result
