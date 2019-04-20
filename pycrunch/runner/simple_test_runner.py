import io
import logging
from collections import namedtuple
import importlib.util
from typing import Iterable

import coverage

from pycrunch.api.serializers import serialize_coverage
from pycrunch.api.shared import timestamp
from . import _abstract_runner
from . import exclusions

logger = logging.getLogger(__name__)

TestMetadata = namedtuple('TestMetadata', ['filename', 'name', 'module'])

class SimpleTestRunner(_abstract_runner.Runner):
    def __init__(self):
        pass

    def run(self, tests):

        results = dict()
        for t in tests:
            cov = self.start_coverage()
            try:
                time_start = timestamp()
                metadata = TestMetadata(**t)
                self._run_test(metadata)
                time_end = timestamp()
                time_elapsed = time_end - time_start
                cov.stop()
                fqn = metadata.module + ':' + metadata.name
                coverage_for_run = serialize_coverage(cov, fqn, time_elapsed)
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
        cov.start()
        logger.debug('-- after coverage.start')
        return cov

    def _run_test(self, test: TestMetadata):
        try:
            logger.debug('before _run_module...')
            spec = importlib.util.spec_from_file_location("fake.name", test.filename)
            logger.debug('  spec_from_file_location -> done; importing module...')

            foo = importlib.util.module_from_spec(spec)

            logger.debug('  module_from_spec -> done; going to exec_module...')
            # logger.warning(f'_run_test->vars {vars(foo)}')
            spec.loader.exec_module(foo)
            method_to_call = getattr(foo, test.name, None)
            if method_to_call:
                method_to_call()
            # logger.debug('after exec_module')
        except Exception as e:
            logger.exception('Error while executing _run_test', exc_info=e)
