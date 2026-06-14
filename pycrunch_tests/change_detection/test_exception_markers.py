"""
T-EM: Tests for M11 — exception marker survival across combined-coverage updates.
"""

from pycrunch.api.serializers import CoverageRun, CoverageRunForSingleFile
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.combined_coverage import CombinedCoverage
from pycrunch.session.recorded_exception import RecordedException


def _make_run(fqn: str, files, succeeded: bool, exception=None) -> CoverageRun:
    er = SingleTestExecutionResult()
    if succeeded:
        er.run_did_succeed()
    else:
        er.run_did_fail()
    if exception is not None:
        er.record_exception(RecordedException(exception[0], exception[1], '', {}))
    run = CoverageRun(fqn, 0, dict(fqn=fqn), er)
    for fname, lines in files:
        run.files.append(CoverageRunForSingleFile(fname, lines))
    return run


def _make_run_no_metadata(fqn: str) -> CoverageRun:
    """Simulates a CoverageRun produced by _fill_missing_results (test_metadata=None, no files)."""
    er = SingleTestExecutionResult()
    er.run_did_fail()
    # recorded_exception stays None — same as create_failed_with_reason path
    return CoverageRun(fqn, -1, None, er)


# ── T-EM-1: success run clears any pre-existing exception marker


def test_success_run_clears_exception_marker():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    # Pre-seed an exception entry as if a previous failed run recorded it
    cov.exceptions.add_exception(fqn, 'file_a.py', 42)
    assert fqn in cov.exceptions.exceptions

    run = _make_run(fqn, [('file_a.py', [1, 2])], succeeded=True, exception=None)
    cov.add_multiple_results({fqn: run})

    assert fqn not in cov.exceptions.exceptions


# ── T-EM-2: failed run WITH recorded_exception stores the marker


def test_failed_run_with_exception_stores_marker():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    run = _make_run(
        fqn, [('file_a.py', [1])], succeeded=False, exception=('file_a.py', 10)
    )
    cov.add_multiple_results({fqn: run})

    assert fqn in cov.exceptions.exceptions
    stored_file, stored_line = cov.exceptions.exceptions[fqn]
    assert stored_file == 'file_a.py'
    assert stored_line == 10


# ── T-EM-3: failed run WITHOUT recorded_exception clears pre-existing marker;
#            test_metadata=None (fill_missing_results path) does not raise


def test_failed_run_without_exception_clears_existing_marker():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    # Pre-seed an exception entry
    cov.exceptions.add_exception(fqn, 'file_a.py', 10)
    assert fqn in cov.exceptions.exceptions

    # test_metadata=None simulates _fill_missing_results (no files, no exception)
    run = _make_run_no_metadata(fqn)
    cov.add_multiple_results({fqn: run})

    assert fqn not in cov.exceptions.exceptions
