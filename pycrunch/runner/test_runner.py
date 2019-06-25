import logging
import sys
import traceback
from collections import namedtuple
import importlib.util
from pprint import pprint

import coverage

from pycrunch.api.serializers import serialize_test_run
from pycrunch.api.shared import timestamp
from pycrunch.runner.interception import capture_stdout
from . import _abstract_runner
from . import exclusions
from pycrunch.shared import TestMetadata

logger = logging.getLogger(__name__)



class TestRunner():
    def __init__(self, runner_engine : _abstract_runner.Runner):
        self.runner_engine = runner_engine

    def run(self, tests):

        results = dict()
        for test_to_run in tests:
            cov = self.start_coverage()
            try:
                with capture_stdout() as get_value:
                    time_start = timestamp()
                    metadata = TestMetadata(**test_to_run)
                    execution_result = self.runner_engine.run_test(metadata)
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
        # logger.debug('-- before coverage.start')

        # comment this line to be able to debug
        cov.start()

        # logger.debug('-- after coverage.start')
        return cov

