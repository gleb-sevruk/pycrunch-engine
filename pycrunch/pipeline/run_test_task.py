from datetime import datetime
from queue import Queue
import time

from pycrunch.api import shared
from pycrunch.api.serializers import serialize_test_run
from pycrunch.api.shared import file_watcher
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.runner.simple_test_runner import SimpleTestRunner
from pycrunch.session.combined_coverage import combined_coverage, CombinedCoverage
from pycrunch.session.state import engine


def serialize_combined_coverage(combined: CombinedCoverage):
    return [
        dict(
            filename=x.filename,
            lines_with_entrypoints=compute_lines(x)) for x in combined.files.values()
    ]


def compute_lines(x):
    zzz = {line_number:list(entry_points) for (line_number, entry_points) in x.lines_with_entrypoints.items()}
    return zzz

    # return result


class RunTestTask(AbstractTask):

    def __init__(self, tests):
        self.timestamp = shared.timestamp()
        self.tests = tests

    def run(self):
        runner = SimpleTestRunner()
        engine.tests_will_run(self.tests)
        with ModuleCleanup() as cleanup:
            results = runner.run(self.tests)

        engine.tests_did_run(results)

        combined_coverage.add_multiple_results(results)

        results_as_json = dict()
        for k,v in results.items():
            results_as_json[k] = v.as_json()


        shared.pipe.push(event_type='test_run_completed',
                         coverage=dict(all_runs=results_as_json),
                         data=self.tests,
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),

        serialized = serialize_combined_coverage(combined_coverage)
        shared.pipe.push(event_type='combined_coverage_updated',
                         combined_coverage=serialized,
                         dependencies={entry_point: list(filenames) for entry_point, filenames in combined_coverage.dependencies.items() },
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),
        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
