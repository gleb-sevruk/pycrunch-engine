import io
import logging

import coverage

from . import _abstract_runner
from . import exclusions

logger = logging.getLogger(__name__)

class SimpleRunner(_abstract_runner.Runner):
    def __init__(self):
        pass

    def run(self, path_to_python_file):
        cov = self.start_coverage()

        self._run_module(path_to_python_file=path_to_python_file)



        # cov.stop()
        # creates .coverage file on disk
        # cov.save()
        # cov.report()

        output_file = io.StringIO()
        percentage = cov.report(file=output_file)
        # this modifies my filer as : playground.py.cover
        # anon = cov.annotate()
        file_getvalue = output_file.getvalue()
        logger.debug(file_getvalue)

        input_file = io.StringIO(output_file.getvalue())
        # coverage_data = cov.get_data()
        # print_coverage(coverage_data, cov)
        return cov

    def start_coverage(self):
        cov = coverage.Coverage(config_file=False, branch=True, omit=exclusions.exclude_list)
        logger.debug('-- before coverage.start')
        # cov.start()
        logger.debug('-- after coverage.start')
        return cov

    def _run_module(self, path_to_python_file):
        try:
            #  Not debuggable if cov.start() called
            logger.debug('before _run_module...')
            import importlib.util
            spec = importlib.util.spec_from_file_location("fake.name", path_to_python_file)
            logger.debug('  spec_from_file_location -> done; importing module...')

            foo = importlib.util.module_from_spec(spec)

            logger.debug('  module_from_spec -> done; going to exec_module...')
            # logger.warning(vars(foo))
            spec.loader.exec_module(foo)
            # execute as following
            # method_to_call = getattr(module, 'test_1')
            logger.debug('after exec_module')
        except Exception as e:
            logger.exception('Error while executing code', exc_info=e)
