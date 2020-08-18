from pycrunch.api.serializers import CoverageRun
from pycrunch.child_runtime.coverage_hal import CoverageAbstraction
from pycrunch.insights.variables_inspection import InsightTimeline, inject_timeline
from pycrunch.runner.execution_result import ExecutionResult

DISABLE_COVERAGE = False

class TestRunner:
    def __init__(self, runner_engine, timeline, child_config):
        self.runner_engine = runner_engine
        self.timeline = timeline
        self.child_config = child_config

    def run(self, tests):
        self.timeline.mark_event('Run: inside run method')
        from pycrunch.introspection.clock import clock
        from pycrunch.runner.interception import capture_stdout
        from pycrunch.shared.primitives import TestMetadata
        self.timeline.mark_event('Run: inside run method - imports complete')

        results = dict()
        for test_to_run in tests:
            self.timeline.begin_nested_interval(f'Running test {test_to_run.get("fqn", "unknown")}')

            # record traced variables
            state_timeline = InsightTimeline(clock=clock)
            state_timeline.start()
            inject_timeline(state_timeline)

            metadata = TestMetadata(**test_to_run)
            try:
                # TODO: Check if starting coverage AFTER pytest.main,
                #    before test_method enter, improves time in magnitudes.
                #  ---
                #    checked, there are 2x improvement for small files (0.06 vs 0.10, but still
                #      slow as before on 500+ tests in one file
                should_disable_coverage = DISABLE_COVERAGE
                if self.child_config.enable_remote_debug:
                    should_disable_coverage = True
                cov = CoverageAbstraction(should_disable_coverage, self.timeline)
                cov.start()

                with capture_stdout() as get_value:
                    time_start = clock.now()
                    self.timeline.mark_event('About to start test execution')
                    execution_result = self.runner_engine.run_test(metadata)
                    self.timeline.mark_event('Test execution complete, postprocessing results')
                    time_end = clock.now()
                    time_elapsed = time_end - time_start

                    cov.stop()

                    captured_output = get_value()
                    self.timeline.mark_event('Received captured output')

                    execution_result.output_did_become_available(captured_output)
                    execution_result.state_timeline_did_become_available(state_timeline)

                    self.timeline.mark_event('Before coverage serialization')
                    coverage_for_run = self.serialize_test_run(cov, metadata.fqn, time_elapsed, test_metadata=test_to_run, execution_result=execution_result)
                    self.timeline.mark_event('After coverage serialization')
            except Exception as e:
                # Here is most likely exception in the engine itself.
                self.timeline.mark_event('Test execution exception.')
                import sys
                tb = self.get_detailed_traceback(metadata.fqn)
                print(tb, file=sys.__stdout__)
                from pycrunch.api.serializers import CoverageRun
                result = ExecutionResult.create_failed_with_reason(tb)
                # inject fake run to not crash entire pipeline
                coverage_for_run = CoverageRun(metadata.fqn, -1, test_to_run, execution_result=result)

                # logger.exception('error during run', exc_info=e)
                
            results[metadata.fqn] = coverage_for_run
            self.timeline.end_nested_interval()
        return results

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



