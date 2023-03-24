import random

from pycrunch.api.serializers import CoverageRun, CoverageRunForSingleFile
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.combined_coverage import (
    CombinedCoverage,
    serialize_combined_coverage,
)
from pycrunch.session.recorded_exception import RecordedException


def test_exception_clears_after_test_removed():
    sut = CombinedCoverage()
    fqn = "fake_test"
    execution_result = SingleTestExecutionResult()
    # generate random line number
    line_number = random.randint(1, 100)

    execution_result.record_exception(
        RecordedException("file1.py", line_number, "ValueError __at__ location", {})
    )
    run = CoverageRun(fqn, 0, dict(fqn=fqn), execution_result)
    run.files.append(CoverageRunForSingleFile("file1.py", [1, 2, 3]))
    to_add = dict()
    to_add[fqn] = run
    sut.add_multiple_results(to_add)

    first_pass = serialize_combined_coverage(sut)
    assert first_pass[0]["filename"] == 'file1.py'
    assert first_pass[0]["exceptions"] == [line_number]

    sut.test_did_removed(fqn)
    second_pass = serialize_combined_coverage(sut)
    assert second_pass[0]["filename"] == 'file1.py'
    assert second_pass[0]["exceptions"] == []
