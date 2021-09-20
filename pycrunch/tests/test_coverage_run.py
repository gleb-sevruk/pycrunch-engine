import unittest
from pprint import pprint
from unittest.mock import MagicMock

from pycrunch.api.serializers import CoverageRun
from pycrunch.child_runtime.coverage_hal import CoverageAbstraction
from pycrunch.insights.variables_inspection import InsightTimeline
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

    def test_coverage_lib_version_4(self):
        sut = self.create_sut(is_v5_or_greater=False)

        assert 'data_file' not in sut.get_coverage_arguments()

    def test_coverage_lib_version_5(self):
        sut = self.create_sut(is_v5_or_greater=True)

        actual = sut.get_coverage_arguments()

        assert 'data_file' in actual
        assert actual['data_file'] == None

    def create_sut(self, is_v5_or_greater):
        sut = CoverageAbstraction(True, None)
        sut.is_coverage_v5_or_greater = MagicMock(return_value=is_v5_or_greater)
        return sut
