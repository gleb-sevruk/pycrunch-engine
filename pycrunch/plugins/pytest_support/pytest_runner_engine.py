import logging
import os
import sys
import traceback
from pprint import pprint

import pytest

from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner import _abstract_runner
from pycrunch.runner.execution_result import ExecutionResult

logger = logging.getLogger(__name__)



class PyTestRunnerEngine(_abstract_runner.Runner):
    def __init__(self):
        # import django
        # django.setup()

        pass

    def run_test(self, test) -> ExecutionResult:
        execution_result = ExecutionResult()
        try:
            # fqn_test_to_run = test.filename + '::' + test.name + ' - PID ' + str(os.getpid())
            fqn_test_to_run = test.filename + '::' + test.name
            # pprint(fqn_test_to_run)
            # pprint(os.getpid())
            plugin = PyTestInterceptionPlugin(tests_to_run=[fqn_test_to_run])

            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
            # print(os.getpid())
            # pprint(dict(passed_tests=plugin.passed_tests))
            # pprint(dict(failed_tests=plugin.failed_tests))

            # print('testing output interception')
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
