# import logging
import re

import coverage


# logger = logging.getLogger(__name__)


DISABLE_COVERAGE = False

class TestRunner():
    def __init__(self, runner_engine, timeline):
        self.timeline = timeline
        self.runner_engine = runner_engine

    def run(self, tests):
        self.timeline.mark_event('Run: inside run method')

        from pycrunch.api.serializers import serialize_test_run
        from pycrunch.api.shared import timestamp
        from pycrunch.runner.interception import capture_stdout
        from pycrunch.shared.models import TestMetadata
        self.timeline.mark_event('Run: inside run method - imports complete')

        results = dict()
        for test_to_run in tests:
            self.timeline.begin_nested_interval(f'Running test {test_to_run.get("fqn", "unknown")}')
            cov = self.start_coverage()
            self.timeline.mark_event('Run: Coverage started')

            try:
                with capture_stdout() as get_value:
                    time_start = timestamp()
                    metadata = TestMetadata(**test_to_run)
                    self.timeline.mark_event('About to start test execution')
                    execution_result = self.runner_engine.run_test(metadata)
                    self.timeline.mark_event('Test execution complete, postprocessing results')
                    time_end = timestamp()
                    time_elapsed = time_end - time_start

                    if not DISABLE_COVERAGE:
                        cov.stop()

                    fqn = metadata.fqn
                    captured_output = get_value()

                    execution_result.output_did_become_available(captured_output)
                    coverage_for_run = serialize_test_run(cov, fqn, time_elapsed, test_metadata=test_to_run, execution_result=execution_result)
            except Exception as e:
                self.timeline.mark_event('Test execution exception.')
                pass
                # logger.exception('error during run', exc_info=e)
            results[fqn] = coverage_for_run
            self.timeline.end_nested_interval()
        return results

    def start_coverage(self):
        from . import exclusions

        use_slow_tracer = False
        # user_slow_tracer = True
        # todo exclusion list should be configurable
        cov = coverage.Coverage(config_file=False, timid=use_slow_tracer, branch=True, omit=exclusions.exclude_list)
        # logger.debug('-- before coverage.start')

        # disable CTracer on this line to be able to debug test execution
        if not DISABLE_COVERAGE:
            cov.start()
        # cov.exclude('def')

        # logger.debug('-- after coverage.start')
        return cov

