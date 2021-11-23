import logging
import os

import pytest

from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner import _abstract_runner

logger = logging.getLogger(__name__)


class PyTestRunnerEngine(_abstract_runner.Runner):
    def _run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        fqn_test_to_run = test.filename + '::' + test.name

        plugin = PyTestInterceptionPlugin([fqn_test_to_run])

        # pytest.main(['tests_two.py:test_x', '-p', 'no:terminal'])
        # q - quiet
        # s - do not capture console logs
        additional_pytest_args = ['-qs']
        plugins_arg = []

        if not self.child_config.load_pytest_plugins:
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = 'True'
            plugins_arg += ['-p', 'no:junitxml']

        # --trace-config
        # , '-p', 'no:helpconfig', - cannot be disabled
        all_args = additional_pytest_args + plugins_arg
        # print(all_args, file=sys.__stdout__)
        pytest.main([fqn_test_to_run] + all_args, plugins=[plugin])

        # pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
        return plugin.guess_run_status(test.name)

