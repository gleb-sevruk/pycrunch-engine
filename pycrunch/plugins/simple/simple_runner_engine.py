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
    def run_test(self, test):
        execution_result = ExecutionResult()
        try:
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
                execution_result.run_did_succeed()
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
