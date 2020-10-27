import logging
import os
import sys
import traceback

import pytest

from pycrunch.runner import _abstract_runner

logger = logging.getLogger(__name__)


class NoseRunnerEngine(_abstract_runner.Runner):
    def _run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        fqn_test_to_run = test.filename + ':' + test.name

        # TODO
        plugin = PyTestInterceptionPlugin([fqn_test_to_run])

        # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
        # q - quiet
        # s - do not capture console logs
        additional_pytest_args = ['-qs']
        plugins_arg = []

        if not self.child_config.load_nose_plugins:
            plugins_arg += ['--nologcapture']

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

        return plugin.guess_run_status(test.name):

