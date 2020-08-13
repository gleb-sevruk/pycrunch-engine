import json
import unittest
from pprint import pprint

from pycrunch.api.serializers import CoverageRun
from pycrunch.insights.variables_inspection import InsightTimeline, trace
from pycrunch.introspection.clock import Clock
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.shared.primitives import TestMetadata


class TestCoverageRun(unittest.TestCase):
    def test_sample(self):
        test_meta = TestMetadata('file1', 'test_a', 'module_a', 'module_a:test_a', 'queued')
        state_timeline = InsightTimeline(clock=Clock())

        execution_result = ExecutionResult()
        execution_result.run_did_succeed()
        execution_result.state_timeline_did_become_available(state_timeline)
        run = CoverageRun('test1', 1, test_meta, execution_result)
        pprint(run.as_json())

