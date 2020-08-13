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
    def __init__(self, child_config):
        """

        :type child_config: pycrunch.child_runtime.child_config.ChildRuntimeConfig
        """
        self.child_config = child_config


    def run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        execution_result = ExecutionResult()
        try:
            fqn_test_to_run = test.filename + '::' + test.name

            plugin = PyTestInterceptionPlugin([fqn_test_to_run])

            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            additional_pytest_args = ['-qs' ]
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
                    import pydevd_pycharm
                    pydevd_pycharm.settrace('127.0.0.1', suspend=False, port=self.child_config.remote_debug_port, stdoutToServer=True, stderrToServer=True)
                except ModuleNotFoundError as e:
                    print('---\nFailed to import pydevd_pycharm', file=sys.__stdout__)
                    print('  Make sure you install pudb pycharm bindings by running:', file=sys.__stdout__)
                    print('pip install pydevd-pycharm\n---', file=sys.__stdout__)
                    raise
            pytest.main([fqn_test_to_run] + all_args, plugins=[plugin])

            # pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])

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

