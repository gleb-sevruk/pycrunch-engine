import logging
import sys
import traceback
from collections import namedtuple
import importlib.util
from pprint import pprint

import coverage

from pycrunch.api.serializers import serialize_test_run
from pycrunch.api.shared import timestamp
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.runner.interception import capture_stdout
from . import _abstract_runner
from . import exclusions

logger = logging.getLogger(__name__)

TestMetadata = namedtuple('TestMetadata', ['filename', 'name', 'module', 'fqn', 'state'])


class SimpleTestRunner(_abstract_runner.Runner):
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

        # output_file = io.StringIO()
        # percentage = cov.report(file=output_file)
        # file_getvalue = output_file.getvalue()
        # logger.debug(file_getvalue)
        #
        # input_file = io.StringIO(output_file.getvalue())
        return results

    def start_coverage(self):
        cov = coverage.Coverage(config_file=False, branch=True, omit=exclusions.exclude_list)
        logger.debug('-- before coverage.start')
        # comment this line to be able to debug
        cov.start()
        logger.debug('-- after coverage.start')
        return cov

    def _run_test(self, test: TestMetadata) -> ExecutionResult:
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
