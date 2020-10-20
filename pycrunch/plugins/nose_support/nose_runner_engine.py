import logging
import sys
import traceback


from pycrunch.runner import _abstract_runner
from pycrunch.runner.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class NoseRunnerEngine(_abstract_runner.Runner):
    def __init__(self, child_config):
        """

        :type child_config: pycrunch.child_runtime.child_config.ChildRuntimeConfig
        """
        self.child_config = child_config


    def run_test(self, test):
        """

        :type test: pycrunch.shared.primitives.TestMetadata
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        execution_result = ExecutionResult()
        try:
            fqn_test_to_run = test.filename + ':' + test.name


            if self.child_config.enable_remote_debug:
                try:
                    import pydevd_pycharm
                    pydevd_pycharm.settrace('127.0.0.1', suspend=False, port=self.child_config.remote_debug_port, stdoutToServer=True, stderrToServer=True)
                except ModuleNotFoundError as e:
                    print('---\nFailed to import pydevd_pycharm', file=sys.__stdout__)
                    print('  Make sure you install pudb pycharm bindings by running:', file=sys.__stdout__)
                    print('pip install pydevd-pycharm\n---', file=sys.__stdout__)
                    raise

            from nose.loader import TestLoader
            from nose import run

            # Example of how to run programmatically from here:
            # https://gist.github.com/jessejlt/2322351
            suite_1 = TestLoader().loadTestsFromName(fqn_test_to_run)
            try:
                # nose reads all argv, and that is not desired behaviour, cut this to 1
                argvs = sys.argv[:1]
                # Don’t capture stdout, we want it to be redirected into pycrunch window.
                argvs.append('--nocapture')
                results = run(suite=suite_1, argv=argvs)
                if results:
                    execution_result.run_did_succeed()
                else:
                    execution_result.run_did_fail()

            except Exception as e:
                print(e)

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

