import logging
import os
import sys
import traceback

import pytest

from pycrunch.plugins.pytest_support.exception_utilities import get_originating_frame_and_location
from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner import _abstract_runner
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.recorded_exception import RecordedException

logger = logging.getLogger(__name__)


class PyTestRunnerEngine(_abstract_runner.Runner):
    def __init__(self, child_config):
        """

        :type child_config: pycrunch.child_runtime.child_config.ChildRuntimeConfig
        """
        self.child_config = child_config


    def run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.SingleTestExecutionResult
        """
        execution_result = SingleTestExecutionResult()
        try:
            fqn_test_to_run = test.filename + '::' + test.name

            plugin = PyTestInterceptionPlugin([fqn_test_to_run])

            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            # l - show variable values in the current stack
            additional_pytest_args = ['-qs', '-l']
            plugins_arg = []

            if not self.child_config.load_pytest_plugins:
                os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = 'True'
                plugins_arg += ['-p', 'no:junitxml']

            # --trace-config
            # , '-p', 'no:helpconfig', - cannot be disabled
            all_args = additional_pytest_args + plugins_arg
            # print(all_args, file=sys.__stdout__)
            if self.child_config.enable_remote_debug:
                try:
                    # Todo: this is too late to check for debugger existence.
                    #   Need verify before `debug` button click
                    import pydevd_pycharm
                    pydevd_pycharm.settrace('127.0.0.1', suspend=False, port=self.child_config.remote_debug_port, stdoutToServer=True, stderrToServer=True)
                except ModuleNotFoundError:
                    print('---\nFailed to import pydevd_pycharm', file=sys.__stdout__)
                    print('  Make sure you install pudb pycharm bindings by running:', file=sys.__stdout__)
                    print('pip install pydevd-pycharm\n---', file=sys.__stdout__)
                    raise
            pytest.main([fqn_test_to_run] + all_args, plugins=[plugin])

            # pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
            if plugin.guess_run_status(test.name):
                execution_result.run_did_succeed()
            else:
                possible_exception = plugin.get_recorded_exception(test.name)
                execution_result.record_exception(possible_exception)
                execution_result.run_did_fail()
        except Exception as e:
            etype, value, current_traceback = sys.exc_info()
            _, filename, line_number, _ = get_originating_frame_and_location(current_traceback)
            execution_result.record_exception(RecordedException(filename, line_number, str(current_traceback), {}))
            execution_result.run_did_fail()
            last_call = -1
            traceback.print_exc(file=sys.stdout)
            traceback.print_exception(etype, value, current_traceback, limit=last_call, file=sys.stdout)
            # print(str(e))
            logger.exception('Error while executing _run_test', exc_info=e)
        return execution_result

