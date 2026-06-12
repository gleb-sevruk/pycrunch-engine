"""
T-SQ: Tests for M9.4 — scheduled tests that produce no result are marked failed.
"""
from pycrunch.api.serializers import CoverageRun
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult


def _make_converted(fqn: str):
    return dict(fqn=fqn, filename='test_mod.py', name=fqn.split(':')[1], module='test_mod', state='converted')


def _make_run(fqn: str, succeeded: bool) -> CoverageRun:
    er = SingleTestExecutionResult()
    if succeeded:
        er.run_did_succeed()
    else:
        er.run_did_fail()
    return CoverageRun(fqn, 0, dict(fqn=fqn), er)


# ── T-SQ-1: run_results missing one fqn → it gets status 'failed'

def test_missing_fqn_marked_failed():
    fqn_a = 'test_mod:test_a'
    fqn_b = 'test_mod:test_b'

    converted = [_make_converted(fqn_a), _make_converted(fqn_b)]
    run_results = {fqn_a: _make_run(fqn_a, succeeded=True)}  # fqn_b missing

    RunTestTask._fill_missing_results(converted, run_results)

    assert fqn_b in run_results
    assert run_results[fqn_b].execution_result.status == 'failed'
    # fqn_a untouched
    assert run_results[fqn_a].execution_result.status == 'success'


# ── T-SQ-2: all fqns returned → no changes

def test_all_fqns_present_no_change():
    fqn_a = 'test_mod:test_a'
    fqn_b = 'test_mod:test_b'

    converted = [_make_converted(fqn_a), _make_converted(fqn_b)]
    run_results = {
        fqn_a: _make_run(fqn_a, succeeded=True),
        fqn_b: _make_run(fqn_b, succeeded=False),
    }

    RunTestTask._fill_missing_results(converted, run_results)

    # Nothing added or changed
    assert len(run_results) == 2
    assert run_results[fqn_a].execution_result.status == 'success'
    assert run_results[fqn_b].execution_result.status == 'failed'
