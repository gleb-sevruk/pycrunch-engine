import logging
import sys

from pycrunch.runner import _abstract_runner

logger = logging.getLogger(__name__)


class NoseRunnerEngine(_abstract_runner.Runner):
    def _run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        fqn_test_to_run = test.filename + ':' + test.name

        from nose.loader import TestLoader
        from nose import run

        # Example of how to run programmatically from here:
        # https://gist.github.com/jessejlt/2322351
        suite_1 = TestLoader().loadTestsFromName(fqn_test_to_run)
        # nose reads all argv, and that is not desired behaviour, cut this to 1
        argvs = sys.argv[:1]
        # Don’t capture stdout, we want it to be redirected into pycrunch window.
        argvs.append('--nocapture')
        results = run(suite=suite_1, argv=argvs)
        return bool(results)
