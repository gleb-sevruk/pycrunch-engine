import importlib.util
import logging
import sys
import traceback

from pycrunch.runner import _abstract_runner
from pycrunch.runner.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class SimpleTestRunnerEngine(_abstract_runner.Runner):
    """
      This class probably is not used anymore. It was for early prototype.
    """
    def _run_test(self, test):
        logger.debug('before _run_module...')
        spec = importlib.util.spec_from_file_location("fake.name", test.filename)
        logger.debug('  spec_from_file_location -> done; importing module...')

        foo = importlib.util.module_from_spec(spec)

        logger.debug('  module_from_spec -> done; going to exec_module...')
        # logger.warning(f'_run_test->vars {vars(foo)}')
        spec.loader.exec_module(foo)
        method_to_call = getattr(foo, test.name, None)
        # print(vars(foo))
        if method_to_call:
            method_to_call()
            return True