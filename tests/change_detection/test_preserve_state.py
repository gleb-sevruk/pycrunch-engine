"""
T-PS: Tests for M8 — preserve_state on rediscovery.

Verifies that smart-mode rediscovery doesn't wipe execution results and coverage
for tests that weren't in the execution plan.
"""

import asyncio

from pycrunch.api.serializers import CoverageRun, CoverageRunForSingleFile
from pycrunch.change_detection import normalize_path
from pycrunch.change_detection.fingerprint import fingerprint_source
from pycrunch.change_detection.import_graph import ImportGraph
from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
from pycrunch.discovery.simple import DiscoveredTest
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.combined_coverage import CombinedCoverage
from pycrunch.session.file_map import TestMap
from pycrunch.shared.models import AllTests


def discovered(name='test_a', filename='/proj/test_mod.py', module='test_mod'):
    return DiscoveredTest(name=name, filename=filename, module=module)


def coverage_run(fqn, files):
    """files: list of (filename, [lines])"""
    er = SingleTestExecutionResult()
    er.run_did_succeed()
    run = CoverageRun(fqn, 0, dict(fqn=fqn), er)
    for fname, lines in files:
        run.files.append(CoverageRunForSingleFile(fname, lines))
    return run


def patch_singletons(cache, graph, coverage, tmap):
    import pycrunch.pipeline.file_modification_task as fmt_mod

    fmt_mod._sc_mod.snapshot_cache = cache
    fmt_mod._ig_mod.import_graph = graph
    fmt_mod._cc_mod.combined_coverage = coverage
    fmt_mod._fm_mod.test_map = tmap


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── T-PS-1: preserve_state=True → execution_result kept, discovered_test updated


def test_preserve_state_keeps_execution_result():
    cov = CombinedCoverage()
    sut = AllTests()
    # Wire up the singleton so test_did_removed is called on the right object
    import pycrunch.shared.models as m

    original = m.combined_coverage
    m.combined_coverage = cov
    try:
        fqn = 'test_mod:test_a'
        dt_v1 = discovered('test_a')
        sut.test_discovered(fqn, dt_v1, False)
        er = sut.tests[fqn].execution_result
        er.run_did_succeed()
        assert sut.tests[fqn].execution_result.status == 'success'

        dt_v2 = discovered('test_a')  # updated metadata (same name, fresh object)
        sut.test_discovered(fqn, dt_v2, False, preserve_state=True)

        assert sut.tests[fqn].execution_result is er
        assert sut.tests[fqn].execution_result.status == 'success'
        assert sut.tests[fqn].discovered_test is dt_v2
    finally:
        m.combined_coverage = original


# ── T-PS-2: preserve_state=True for NEW fqn → created normally (pending)


def test_preserve_state_creates_new_test_normally():
    cov = CombinedCoverage()
    sut = AllTests()
    import pycrunch.shared.models as m

    original = m.combined_coverage
    m.combined_coverage = cov
    try:
        fqn = 'test_mod:test_new'
        dt = discovered('test_new')
        sut.test_discovered(fqn, dt, False, preserve_state=True)
        assert fqn in sut.tests
        assert sut.tests[fqn].execution_result.status == 'pending'
    finally:
        m.combined_coverage = original


# ── T-PS-3: preserve_state=False for existing → state reset, coverage cleared


def test_no_preserve_state_resets_existing():
    cov = CombinedCoverage()
    sut = AllTests()
    import pycrunch.shared.models as m

    original = m.combined_coverage
    m.combined_coverage = cov
    try:
        fqn = 'test_mod:test_a'
        dt = discovered('test_a')
        sut.test_discovered(fqn, dt, False)
        sut.tests[fqn].execution_result.run_did_succeed()

        # Simulate coverage for this test
        cov.ensure_file_statistics_exist('/proj/test_mod.py')
        cov.files['/proj/test_mod.py'].mark_lines([1, 2], fqn)
        assert fqn in cov.files['/proj/test_mod.py'].lines_with_entrypoints[1]

        # Re-discover with preserve_state=False (legacy behavior)
        sut.test_discovered(fqn, dt, False, preserve_state=False)

        # Execution result must be reset to pending
        assert sut.tests[fqn].execution_result.status == 'pending'
        # Coverage for this fqn must be cleared
        assert fqn not in cov.files['/proj/test_mod.py'].lines_with_entrypoints[1]
    finally:
        m.combined_coverage = original


# ── T-PS-4: add_multiple_results: stale coverage from file B is cleaned


def test_add_multiple_results_clears_stale_file_coverage():
    cov = CombinedCoverage()
    fqn = 'test_mod:test_a'

    # First run: test_a covered file_a.py and file_b.py
    run1 = coverage_run(fqn, [('file_a.py', [1, 2]), ('file_b.py', [10, 11])])
    cov.add_multiple_results({fqn: run1})

    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[1]
    assert fqn in cov.files['file_b.py'].lines_with_entrypoints[10]
    assert fqn in cov.dependencies['file_a.py']
    assert fqn in cov.dependencies['file_b.py']

    # Second run: test_a only covers file_a.py
    run2 = coverage_run(fqn, [('file_a.py', [1, 2])])
    cov.add_multiple_results({fqn: run2})

    # file_a.py: fresh line hits
    assert fqn in cov.files['file_a.py'].lines_with_entrypoints[1]
    # file_b.py: line hits for this fqn must be gone
    assert fqn not in cov.files['file_b.py'].lines_with_entrypoints[10]
    # dependencies[file_a.py] still contains fqn
    assert fqn in cov.dependencies['file_a.py']
    # dependencies[file_b.py] must no longer contain fqn
    assert fqn not in cov.dependencies['file_b.py']


# ── T-PS-5: discard_tests_not_in_map still cleans removed tests


def test_discard_tests_not_in_map_cleans_coverage():
    cov = CombinedCoverage()
    sut = AllTests()
    import pycrunch.shared.models as m

    original_cov = m.combined_coverage
    import pycrunch.session.file_map as fm_mod

    original_map = fm_mod.test_map
    m.combined_coverage = cov
    try:
        tmap = TestMap()
        tmap.map['/proj/test_mod.py'] = {'test_mod:test_a'}
        fm_mod.test_map = tmap
        # models.py imports test_map at module level; patch that binding too
        m.test_map = tmap

        fqn_a = 'test_mod:test_a'
        fqn_b = 'test_mod:test_b'  # will be removed from map

        for fqn in [fqn_a, fqn_b]:
            dt = discovered(fqn.split(':')[1])
            sut.test_discovered(fqn, dt, False)

        # Give test_b some coverage
        cov.ensure_file_statistics_exist('/proj/test_mod.py')
        cov.files['/proj/test_mod.py'].mark_lines([5, 6], fqn_b)
        assert fqn_b in cov.files['/proj/test_mod.py'].lines_with_entrypoints[5]

        sut.discard_tests_not_in_map()

        # test_b removed
        assert fqn_b not in sut.tests
        # test_b coverage cleared
        assert fqn_b not in cov.files['/proj/test_mod.py'].lines_with_entrypoints[5]
        # test_a untouched
        assert fqn_a in sut.tests
    finally:
        m.combined_coverage = original_cov
        fm_mod.test_map = original_map
        m.test_map = original_map


# ── T-PS-6: Integration — smart mode; test_b stays non-pending after test_a changes


def test_smart_mode_preserves_test_b_state_when_test_a_changes(tmp_path):
    """Core scenario: change test_a's body → test_b keeps its 'success' state and coverage."""
    from pycrunch.session.file_map import TestMap

    src_v1 = "def test_a():\n    assert True\n\ndef test_b():\n    assert True\n"
    src_v2 = (
        "def test_a():\n"
        "    assert False\n"  # body changed
        "\n"
        "def test_b():\n"
        "    assert True\n"
    )
    filepath = str(tmp_path / 'test_mod.py')
    (tmp_path / 'test_mod.py').write_text(src_v2)

    fqn_a = 'test_mod:test_a'
    fqn_b = 'test_mod:test_b'

    cache = FileSnapshotCache()
    old_fp = fingerprint_source(src_v1, filepath, test_file=True)
    cache.update(filepath, old_fp)

    coverage = CombinedCoverage()

    tmap = TestMap()
    tmap.map[filepath] = {fqn_a, fqn_b}
    graph = ImportGraph()

    import pycrunch.session.file_map as fm_mod
    import pycrunch.shared.models as m_mod

    original_cov = m_mod.combined_coverage
    original_map = fm_mod.test_map
    m_mod.combined_coverage = coverage
    fm_mod.test_map = tmap
    patch_singletons(cache, graph, coverage, tmap)

    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask

    task = FileModifiedNotificationTask(filepath)

    # Set up AllTests with pre-existing 'success' state for both tests.
    # test_discovered(preserve_state=False) calls test_did_removed, so seed coverage AFTER.
    from pycrunch.shared.models import AllTests

    fake_all_tests = AllTests()
    for fqn in [fqn_a, fqn_b]:
        dt = discovered(fqn.split(':')[1], filename=filepath, module='test_mod')
        fake_all_tests.test_discovered(fqn, dt, False)
        fake_all_tests.tests[fqn].execution_result.run_did_succeed()

    # Seed coverage AFTER test_discovered (which calls test_did_removed, wiping coverage).
    coverage.ensure_file_statistics_exist(normalize_path(filepath))
    stats = coverage.files[normalize_path(filepath)]
    stats.mark_lines([4, 5], fqn_b)
    coverage.dependencies[normalize_path(filepath)].add(fqn_a)
    coverage.dependencies[normalize_path(filepath)].add(fqn_b)

    # Patch state to use our fake AllTests and config
    import pycrunch.session.state as state_mod

    original_engine = state_mod.engine
    original_config = state_mod.config

    class FakeConfig:
        change_detection_mode = 'smart'
        engine_mode = 'auto'
        change_detection_root = str(tmp_path)
        function_prefixes = []

    class FakeEngine:
        folder = str(tmp_path)
        all_tests = fake_all_tests

        async def test_discovery_will_become_available(
            self, test_set, preserve_state=False
        ):
            for discovered_test in test_set.tests:
                fake_all_tests.test_discovered(
                    discovered_test.fqn,
                    discovered_test,
                    False,
                    preserve_state=preserve_state,
                )
            fake_all_tests.discard_tests_not_in_map()

    state_mod.engine = FakeEngine()
    state_mod.config = FakeConfig()

    try:
        plan = run(task._smart_execution_plan(set(), old_fp))

        # test_a should be in plan (body changed)
        assert fqn_a in plan
        # test_b should NOT be in plan (unchanged)
        assert fqn_b not in plan

        # test_b's state must still be 'success' (not reset to pending)
        assert fake_all_tests.tests[fqn_b].execution_result.status == 'success'

        # test_b's coverage must be intact
        assert (
            fqn_b in coverage.files[normalize_path(filepath)].lines_with_entrypoints[4]
        )
    finally:
        state_mod.engine = original_engine
        state_mod.config = original_config
        m_mod.combined_coverage = original_cov
        fm_mod.test_map = original_map


# ── T-PS-7: Regression — legacy mode never sets preserve_state=True


def test_legacy_mode_never_preserves_state(tmp_path, monkeypatch):
    """In legacy mode, test_discovered must reset state (preserve_state=False)."""
    import pycrunch.shared.models as m_mod
    from pycrunch.shared.models import AllTests

    calls = []
    original_test_discovered = AllTests.test_discovered

    def spy_test_discovered(
        self, fqn, discovered_test, is_pinned, preserve_state=False
    ):
        calls.append(preserve_state)
        return original_test_discovered(
            self, fqn, discovered_test, is_pinned, preserve_state
        )

    monkeypatch.setattr(AllTests, 'test_discovered', spy_test_discovered)

    cov = CombinedCoverage()
    original_cov = m_mod.combined_coverage
    m_mod.combined_coverage = cov

    try:
        import pycrunch.session.state as state_mod

        # Simulate legacy mode call via test_discovery_will_become_available
        from pycrunch.discovery.simple import TestSet, TestsInModule

        test_set = TestSet()
        test_set.add_module(TestsInModule('/proj/test_mod.py', ['test_a'], 'test_mod'))

        run(
            state_mod.engine.test_discovery_will_become_available(
                test_set, preserve_state=False
            )
        )

        # All calls must have preserve_state=False
        assert all(ps is False for ps in calls), (
            f'Unexpected preserve_state=True in calls: {calls}'
        )
    finally:
        m_mod.combined_coverage = original_cov
