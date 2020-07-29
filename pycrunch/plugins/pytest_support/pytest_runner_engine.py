import logging
import os
import sys
import traceback

import pytest

from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner import _abstract_runner
from pycrunch.runner.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class PyTestRunnerEngine(_abstract_runner.Runner):
    def run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        execution_result = ExecutionResult()
        try:
            # from pycrunch_trace.client.api import Trace
            # x = Trace()
            # x.start(session_name='runtest2_final')
            # fqn_test_to_run = test.filename + '::' + test.name + ' - PID ' + str(os.getpid())
            fqn_test_to_run = test.filename + '::' + test.name
            # pprint(fqn_test_to_run)
            # pprint(os.getpid())

            plugin = PyTestInterceptionPlugin([fqn_test_to_run])

            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            # TODO v1.1 : this should be customizable in config
            #  We do not want to disable async plugins for example
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = 'True'
            # --trace-config
            # , '-p', 'no:helpconfig', - cannot be disabled
            additional_pytest_args = ['-qs', '-p', 'no:junitxml' ]
            pytest.main([fqn_test_to_run ] + additional_pytest_args , plugins=[plugin])
            # pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
            # print(os.getpid())
            # pprint(dict(passed_tests=plugin.passed_tests))
            # pprint(dict(failed_tests=plugin.failed_tests))

            # print('testing output interception')
            # print(vars(foo))
            if plugin.guess_run_status(test.name):
                execution_result.run_did_succeed()
            else:
                execution_result.run_did_fail()
            # x.stop()
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

