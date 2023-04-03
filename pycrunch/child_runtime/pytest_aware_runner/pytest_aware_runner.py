import datetime
import os
import sys
import traceback
from pprint import pprint
from typing import List, Dict

import pytest

from pycrunch.api.serializers import CoverageRun
from pycrunch.child_runtime.coverage_hal import CoverageAbstraction
from pycrunch.child_runtime.pytest_aware_runner.session_aware_interception_plugin import \
    PyTestSessionAwarePycrunchPlugin
from pycrunch.insights.variables_inspection import InsightTimeline, inject_timeline
from pycrunch.plugins.pytest_support.exception_utilities import get_originating_frame_and_location
from pycrunch.plugins.pytest_support.interception_plugin import PyTestInterceptionPlugin
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.recorded_exception import RecordedException
from pycrunch.shared.primitives import TestMetadata




def array_for_pytest_main(test_to_run: Dict) -> List[str]:
    results = []
    for test in test_to_run:
        metadata = TestMetadata(**test)

        results.append(metadata.filename + '::' + metadata.name)
    return results


class PytestAwareTestRunner:
    def __init__(self, timeline, coverage_exclusions, child_config):
        self.timeline = timeline
        self.child_config = child_config
        self.coverage_exclusions = coverage_exclusions
        self.plugin = PyTestSessionAwarePycrunchPlugin(self.timeline, child_config, coverage_exclusions)


    def run(self, tests) -> Dict[str, CoverageRun]:
        """
        Returns a dictionary of test_fqns to coverage run
        @param tests:
        @return:
        """
        self.timeline.mark_event('Run: inside run method')
        from pycrunch.introspection.clock import clock
        from pycrunch.runner.interception import capture_stdout
        from pycrunch.shared.primitives import TestMetadata
        self.timeline.mark_event('Run: inside run method - imports complete')

        results = dict()
        fqns = array_for_pytest_main(tests)


        all_args = self.get_pytest_args()
        # test_metas = []
        # for test in tests:
        #     metadata = TestMetadata(**test)
        #     test_metas.append(metadata)
        print('Running tests: ')
        pprint(tests)
        self.plugin.tests_will_run(tests)
        self.attach_remote_debugger_if_required()

        pytest.main(fqns + all_args, plugins=[self.plugin])

        results = self.plugin.get_results()
        self.timeline.mark_event('!-- pytest.main complete')
        # self.old_loop(results, tests)
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=50147, stdoutToServer=True, stderrToServer=True)
        return results

    def attach_remote_debugger_if_required(self):
        if self.child_config.enable_remote_debug:
            try:
                # Todo: this is too late to check for debugger existence.
                #   Need verify before `debug` button click
                #  TODO [1.5.2] : enable after release
                import pydevd_pycharm
                pydevd_pycharm.settrace('127.0.0.1', suspend=False, port=self.child_config.remote_debug_port,
                                        stdoutToServer=True, stderrToServer=True)
            except ModuleNotFoundError as e:
                print('---\nFailed to import pydevd_pycharm', file=sys.__stdout__)
                print('  Make sure you install pudb pycharm bindings by running:', file=sys.__stdout__)
                print('pip install pydevd-pycharm\n---', file=sys.__stdout__)
                raise

    def get_pytest_args(self):
        additional_pytest_args = ['-qs', '-l']
        plugins_arg = []
        if not self.child_config.load_pytest_plugins:
            os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = 'True'
            plugins_arg += ['-p', 'no:junitxml']
        # --trace-config
        # , '-p', 'no:helpconfig', - cannot be disabled
        all_args = additional_pytest_args + plugins_arg
        return all_args

    def old_loop(self, results, tests):
        from pycrunch.introspection.clock import clock
        from pycrunch.runner.interception import capture_stdout
        from pycrunch.shared.primitives import TestMetadata

        for test_to_run in tests:
            self.timeline.begin_nested_interval(f'Running test {test_to_run.get("fqn", "unknown")}')

            # record traced variables

            metadata = TestMetadata(**test_to_run)
            try:
                # TODO: Check if starting coverage AFTER pytest.main,
                #    before test_method enter, improves time in magnitudes.
                #  ---
                #    checked, there are 2x improvement for small files (0.06 vs 0.10, but still
                #      slow as before on 500+ tests in one file

                with capture_stdout(should_disable=True) as get_value:
                    time_start = clock.now()
                    self.timeline.mark_event('About to start test execution')
                    execution_result = self.run_test(metadata)  # type: SingleTestExecutionResult
                    self.timeline.mark_event('Test execution complete, postprocessing results')
                    time_end = clock.now()
                    time_elapsed = time_end - time_start

                    _now = datetime.datetime.now()

                    print(f'{os.linesep}at {_now.strftime("%X.%f")[:-3]} {_now.strftime("%x")}')

                    captured_output = get_value()
                    self.timeline.mark_event('Received captured output')

                    execution_result.output_did_become_available(captured_output)
                    execution_result.state_timeline_did_become_available(state_timeline)

                    self.timeline.mark_event('Before coverage serialization')
                    coverage_for_run = self.serialize_test_run(cov, metadata.fqn, time_elapsed,
                                                               test_metadata=test_to_run,
                                                               execution_result=execution_result)
                    self.timeline.mark_event('After coverage serialization')
            except Exception as e:
                # Here is most likely exception in the engine itself.
                self.timeline.mark_event('Test execution exception.')
                import sys
                tb = self.get_detailed_traceback(metadata.fqn)
                print(tb, file=sys.__stdout__)
                from pycrunch.api.serializers import CoverageRun
                result = SingleTestExecutionResult.create_failed_with_reason(tb)
                # inject fake run to not crash entire pipeline
                coverage_for_run = CoverageRun(metadata.fqn, -1, test_to_run, execution_result=result)

                # logger.exception('error during run', exc_info=e)

            results[metadata.fqn] = coverage_for_run
            self.timeline.end_nested_interval()

    def serialize_test_run(self, cov, fqn, time_elapsed, test_metadata, execution_result):
        """
        :type cov: CoverageAbstraction
        :param time_elapsed: float
        :param fqn: str
        """
        run_results = CoverageRun(fqn, time_elapsed, test_metadata, execution_result)
        run_results.store_files_coverage(cov.parse_all_hit_lines())
        return run_results


    def get_detailed_traceback(self, fqn):
        """

        :type fqn: str
        :return str
        """
        import traceback
        from io import StringIO
        out = StringIO()
        print('----', file=out)
        print('Error in PyCrunch subprocess executor ', file=out)
        print(f'   while running test `{fqn}`', file=out)
        print('----', file=out)
        traceback.print_exc(file=out)
        return out.getvalue()

    def run_test(self, test):
        """

        :type test: object
        :return val pycrunch.runner.execution_result.SingleTestExecutionResult
        """
        execution_result = SingleTestExecutionResult()
        try:


            # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
            # q - quite
            # s - do not capture console logs
            # l - show variable values in the current stack
            all_args = self.get_pytest_args()
            # print(all_args, file=sys.__stdout__)

            pytest.main([fqn_test_to_run] + all_args, plugins=[plugin])

            # pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])
            if plugin.guess_run_status(test.name):
                execution_result.run_did_succeed()
            else:
                possible_exception = plugin.get_recorded_exception(test.name)
                execution_result.record_exception(possible_exception)
                execution_result.run_did_fail()
        except Exception as e:
            etype, value, current_traceback = sys.exc_info()
            _, filename, line_number, _ = get_originating_frame_and_location(current_traceback)
            execution_result.record_exception(RecordedException(filename, line_number, str(current_traceback), {}))
            execution_result.run_did_fail()
            last_call = -1
            traceback.print_exc(file=sys.stdout)
            traceback.print_exception(etype, value, current_traceback, limit=last_call, file=sys.stdout)
            # print(str(e))
            import logging
            logger = logging.getLogger(__name__)
            logger.exception('Error while executing _run_test', exc_info=e)
        return execution_result

