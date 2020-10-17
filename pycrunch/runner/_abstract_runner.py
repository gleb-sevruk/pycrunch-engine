import abc
import logging
import sys
import traceback

from pycrunch.runner.execution_result import ExecutionResult

logger = logging.getLogger(__name__)


class Runner(abc.ABC):
    def __init__(self, child_config):
        """

        :type child_config: pycrunch.child_runtime.child_config.ChildRuntimeConfig
        """
        self.child_config = child_config

    @abc.abstractmethod
    def _run_test(self, test):
        """To be provided by specific plugin implementation

        :type test: object
        :return  bool
        """
        pass

    def run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.ExecutionResult
        """
        execution_result = ExecutionResult()
        try:
            if self.child_config.enable_remote_debug:
                try:
                    import pydevd_pycharm
                    pydevd_pycharm.settrace('127.0.0.1', suspend=False, port=self.child_config.remote_debug_port,
                                            stdoutToServer=True, stderrToServer=True)
                except ModuleNotFoundError as e:
                    print('---\nFailed to import pydevd_pycharm', file=sys.__stdout__)
                    print('  Make sure you install pudb pycharm bindings by running:', file=sys.__stdout__)
                    print('pip install pydevd-pycharm\n---', file=sys.__stdout__)
                    raise
            if self._run_test(test):
                execution_result.run_did_succeed()
            else:
                execution_result.run_did_fail()
            # x.stop()
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
