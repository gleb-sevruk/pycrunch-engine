"""
T-FR: Tests for M9.3 — failed-run coverage policy + greedy failed re-run.
"""

import asyncio

from pycrunch.api.serializers import CoverageRun, CoverageRunForSingleFile
from pycrunch.change_detection import normalize_path
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.combined_coverage import CombinedCoverage


def _make_run(fqn: str, files, succeeded: bool) -> CoverageRun:
    er = SingleTestExecutionResult()
    if succeeded:
        er.run_did_succeed()
    else:
        er.run_did_fail()
    run = CoverageRun(fqn, 0, dict(fqn=fqn), er)
    for fname, lines in files:
        run.files.append(CoverageRunForSingleFile(fname, lines))
    return run


# ── T-FR-1: add_multiple_results with failed run —
#   dependencies preserved, gutter shows LAST run only


def test_failed_run_preserves_deps_but_shows_real_lines():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    # Initial success run: covered file_a lines 1-3, file_b lines 10-11
    run_success = _make_run(
        fqn, [('file_a.py', [1, 2, 3]), ('file_b.py', [10, 11])], succeeded=True
    )
    cov.add_multiple_results({fqn: run_success})

    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[1]
    assert fqn in cov.files['file_b.py'].lines_with_entrypoints[10]
    assert fqn in cov.dependencies['file_a.py']
    assert fqn in cov.dependencies['file_b.py']

    # Failed run: only covered file_a line 1 (import failed partway through)
    run_failed = _make_run(fqn, [('file_a.py', [1])], succeeded=False)
    cov.add_multiple_results({fqn: run_failed})

    # (a) Dependency edges survive failure — engine can still re-trigger test
    assert fqn in cov.dependencies['file_b.py']

    # (b) file_b gutter cleared — it wasn't touched in the failed run (stale cleanup)
    assert fqn not in cov.files['file_b.py'].lines_with_entrypoints[10]

    # (c) file_a gutter shows LAST run only: line 1 present, lines 2-3 gone
    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[1]
    assert fqn not in cov.files['file_a.py'].lines_with_entrypoints[2]
    assert fqn not in cov.files['file_a.py'].lines_with_entrypoints[3]


# ── T-FR-2: success run after failed run — wipe + clean replacement


def test_success_after_failed_restores_invariant():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    run_success_v1 = _make_run(
        fqn, [('file_a.py', [1, 2, 3]), ('file_b.py', [10])], succeeded=True
    )
    cov.add_multiple_results({fqn: run_success_v1})

    run_failed = _make_run(fqn, [('file_a.py', [1])], succeeded=False)
    cov.add_multiple_results({fqn: run_failed})

    # Now a clean success: only file_a lines 1-2
    run_success_v2 = _make_run(fqn, [('file_a.py', [1, 2])], succeeded=True)
    cov.add_multiple_results({fqn: run_success_v2})

    # file_b coverage must be gone (wiped by success)
    assert fqn not in cov.files['file_b.py'].lines_with_entrypoints[10]
    assert fqn not in cov.dependencies['file_b.py']
    # file_a line 3 gone (not in v2 run)
    assert fqn not in cov.files['file_a.py'].lines_with_entrypoints[3]
    # Lines 1-2 present
    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[1]
    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[2]


# ── T-FR-3: Full repro — success test_a on module_b → failed run (import error) →
#            fix body in module_b → test_a still in plan via greedy-failed + deps intact


def test_full_repro_greedy_failed_and_deps_preserved(tmp_path):
    from pycrunch.change_detection.fingerprint import compute_file_fingerprint
    from pycrunch.change_detection.import_graph import ImportGraph
    from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
    from pycrunch.discovery.simple import DiscoveredTest
    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask
    from pycrunch.session.file_map import TestMap
    from pycrunch.shared.models import AllTests

    # module_b v1 (good body), v2 (changed body — fix after failure)
    mod_b_v1 = "def helper():\n    return 1\n"
    mod_b_v2 = "def helper():\n    return 2\n"

    mod_b_path = str(tmp_path / 'module_b.py')
    test_file_path = str(tmp_path / 'test_a.py')
    (tmp_path / 'module_b.py').write_text(mod_b_v2)

    fqn_a = 'test_a:test_a'

    cache = FileSnapshotCache()
    old_fp = compute_file_fingerprint(mod_b_v1, mod_b_path)
    cache.update(mod_b_path, old_fp, mod_b_v1)

    cov = CombinedCoverage()

    # Success run: test_a covered module_b lines 1-2
    run_success = _make_run(
        fqn_a, [(mod_b_path, [1, 2]), (test_file_path, [1, 2])], succeeded=True
    )
    cov.add_multiple_results({fqn_a: run_success})

    assert fqn_a in cov.dependencies[mod_b_path]

    # Failed run after syntax break (import error — only sees first line of module_b)
    run_failed = _make_run(fqn_a, [(mod_b_path, [1])], succeeded=False)
    cov.add_multiple_results({fqn_a: run_failed})

    # Deps on module_b must still be intact after failed run
    assert fqn_a in cov.dependencies[mod_b_path], (
        "deps on module_b must survive failed run"
    )

    tmap = TestMap()
    tmap.map[test_file_path] = {fqn_a}
    graph = ImportGraph()

    import pycrunch.pipeline.file_modification_task as fmt_mod
    import pycrunch.session.file_map as fm_mod
    import pycrunch.shared.models as m_mod

    fmt_mod._sc_mod.snapshot_cache = cache
    fmt_mod._ig_mod.import_graph = graph
    fmt_mod._cc_mod.combined_coverage = cov
    fmt_mod._fm_mod.test_map = tmap
    m_mod.combined_coverage = cov
    fm_mod.test_map = tmap

    import pycrunch.session.state as state_mod

    fake_all_tests = AllTests()
    dt = DiscoveredTest(name='test_a', filename=test_file_path, module='test_a')
    fake_all_tests.test_discovered(fqn_a, dt, False)
    fake_all_tests.tests[fqn_a].execution_result.run_did_fail()
    # Re-seed coverage (test_discovered wiped it via test_did_removed)
    cov.ensure_file_statistics_exist(mod_b_path)
    cov.files[mod_b_path].lines_with_entrypoints[1] = {fqn_a}
    cov.files[mod_b_path].lines_with_entrypoints[2] = {fqn_a}
    cov.dependencies[mod_b_path].add(fqn_a)

    original_engine = state_mod.engine
    original_config = state_mod.config

    class FakeConfig:
        change_detection_mode = 'smart'
        engine_mode = 'auto'
        change_detection_root = str(tmp_path)
        function_prefixes = []
        effective_function_prefixes = ('test_',)

    class FakeEngine:
        folder = str(tmp_path)
        all_tests = fake_all_tests

        async def test_discovery_will_become_available(
            self, test_set, preserve_state=False
        ):
            pass

    state_mod.engine = FakeEngine()
    state_mod.config = FakeConfig()

    try:
        plan = asyncio.get_event_loop().run_until_complete(
            FileModifiedNotificationTask(mod_b_path)._smart_execution_plan(
                set(), old_fp
            )
        )
        # test_a must be in plan: body changed (BodyOnlyChange) + greedy-failed
        assert fqn_a in plan
        # deps on module_b must still be present
        assert (
            fqn_a in cov.dependencies[mod_b_path]
            or fqn_a in cov.dependencies[normalize_path(mod_b_path)]
        )
    finally:
        state_mod.engine = original_engine
        state_mod.config = original_config
        m_mod.combined_coverage = __import__(
            'pycrunch.session.combined_coverage', fromlist=['combined_coverage']
        ).combined_coverage
        fm_mod.test_map = __import__(
            'pycrunch.session.file_map', fromlist=['test_map']
        ).test_map

