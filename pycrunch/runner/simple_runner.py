import io
import logging

import coverage

from . import _abstract_runner
from . import exclusions

logger = logging.getLogger(__name__)

class SimpleRunner(_abstract_runner.Runner):
    def __init__(self, exclude_list: list = None):
        self.exclude_list = exclude_list
        if not exclude_list:
            self.exclude_list = exclusions.exclude_list


    def run(self, path_to_python_file):
        cov = coverage.Coverage(config_file=False, branch=True, omit=self.exclude_list)
        logger.debug('SimpleRunner - 2')
        cov.start()
        logger.debug('SimpleRunner - 3')

        # self._run_module(path_to_python_file)
        self._run_module(path_to_python_file=path_to_python_file)
        logger.debug('SimpleRunner - 4')


        cov.stop()
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

    def _run_module(self, path_to_python_file):
        try:
            #  Not debuggable if cov.start() called
            logger.debug('SimpleRunner - 3.1')
            import importlib.util
            spec = importlib.util.spec_from_file_location("fake.name", path_to_python_file)
            logger.debug('SimpleRunner - 3.2')
            foo = importlib.util.module_from_spec(spec)
            logger.debug('SimpleRunner - 3.3')
            spec.loader.exec_module(foo)
            logger.debug('SimpleRunner - 3.4')
            # xx = foo.my_sum()
            logger.debug('SimpleRunner - 3.5')
            # logger.debug(f'xx  + {xx}')
        except Exception as e:
            logger.exception('Error while executing code', exc_info=e)
