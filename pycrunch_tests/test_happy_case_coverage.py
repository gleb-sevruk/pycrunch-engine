"""
T-HC: Regression tests for coverage happy-case scenarios.
"""
import asyncio

from pycrunch.api.serializers import CoverageRun, CoverageRunForSingleFile
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.combined_coverage import CombinedCoverage


def _make_run(fqn: str, files, succeeded: bool = True) -> CoverageRun:
    er = SingleTestExecutionResult()
    if succeeded:
        er.run_did_succeed()
    else:
        er.run_did_fail()
    run = CoverageRun(fqn, 0, dict(fqn=fqn), er)
    for fname, lines in files:
        run.files.append(CoverageRunForSingleFile(fname, lines))
    return run


# ── T-HC-1: Full coverage lifecycle after a file edit:
#   1. Successful run → lines recorded
#   2. File edit (_smart_execution_plan)
#   3. Second successful run with NEW lines → lines updated, object remains defaultdict

def test_coverage_lifecycle_after_edit(tmp_path):
    from pycrunch.change_detection import normalize_path
    from pycrunch.change_detection.fingerprint import compute_file_fingerprint
    from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
    from pycrunch.change_detection.import_graph import ImportGraph
    from pycrunch.session.file_map import TestMap
    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask
    from pycrunch.shared.models import AllTests
    from pycrunch.discovery.simple import DiscoveredTest

    src_v1 = (
        "def test_a():\n"
        "    x = 1\n"
        "    assert x == 1\n"
    )
    src_v2 = (
        "def test_a():\n"
        "    x = 2\n"      # body changed — lines 2-3 still in test
        "    assert x == 2\n"
    )

    filepath = str(tmp_path / 'test_mod.py')
    fqn_a = 'test_mod:test_a'
    norm = normalize_path(filepath)

    # Step 1: first successful run, coverage on lines 1-3
    coverage = CombinedCoverage()
    run1 = _make_run(fqn_a, [(filepath, [1, 2, 3])], succeeded=True)
    coverage.add_multiple_results({fqn_a: run1})

    assert fqn_a in coverage.files[filepath].lines_with_entrypoints[1]
    assert fqn_a in coverage.files[filepath].lines_with_entrypoints[2]

    # Step 2: file edit — _smart_execution_plan (src_v1 → src_v2)
    (tmp_path / 'test_mod.py').write_text(src_v2)

    cache = FileSnapshotCache()
    old_fp = compute_file_fingerprint(src_v1, filepath, test_file=True)
    cache.update(filepath, old_fp, src_v1)

    tmap = TestMap()
    tmap.map[filepath] = {fqn_a}
    graph = ImportGraph()

    import pycrunch.pipeline.file_modification_task as fmt_mod
    import pycrunch.shared.models as m_mod
    import pycrunch.session.file_map as fm_mod
    fmt_mod._sc_mod.snapshot_cache = cache
    fmt_mod._ig_mod.import_graph = graph
    fmt_mod._cc_mod.combined_coverage = coverage
    fmt_mod._fm_mod.test_map = tmap
    m_mod.combined_coverage = coverage
    fm_mod.test_map = tmap

    import pycrunch.session.state as state_mod

    fake_all_tests = AllTests()
    dt = DiscoveredTest(name='test_a', filename=filepath, module='test_mod')
    fake_all_tests.test_discovered(fqn_a, dt, False)
    fake_all_tests.tests[fqn_a].execution_result.run_did_succeed()
    # Re-seed coverage lines after test_discovered cleared them
    coverage.ensure_file_statistics_exist(filepath)
    for line in [1, 2, 3]:
        coverage.files[filepath].lines_with_entrypoints[line].add(fqn_a)
    coverage.dependencies[filepath].add(fqn_a)

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
        async def test_discovery_will_become_available(self, test_set, preserve_state=False):
            pass

    state_mod.engine = FakeEngine()
    state_mod.config = FakeConfig()

    try:
        plan = asyncio.get_event_loop().run_until_complete(
            FileModifiedNotificationTask(filepath)._smart_execution_plan(set(), old_fp)
        )

        # test_a body changed → in plan
        assert fqn_a in plan

        # Step 3: second successful run, same lines 1-3 in new code
        run2 = _make_run(fqn_a, [(filepath, [1, 2, 3])], succeeded=True)
        # Must not raise — this was the bug if lines_with_entrypoints was a plain dict
        coverage.add_multiple_results({fqn_a: run2})

        # New lines recorded correctly
        assert fqn_a in coverage.files[filepath].lines_with_entrypoints[1]
        assert fqn_a in coverage.files[filepath].lines_with_entrypoints[2]
        assert fqn_a in coverage.files[filepath].lines_with_entrypoints[3]

        # lines_with_entrypoints must behave as defaultdict: unknown key returns empty set
        unknown_key_value = coverage.files[filepath].lines_with_entrypoints[999]
        assert unknown_key_value == set(), f'Expected empty set, got {unknown_key_value!r}'
        # Must not raise KeyError on second access of same unknown key
        _ = coverage.files[filepath].lines_with_entrypoints[999]

    finally:
        state_mod.engine = original_engine
        state_mod.config = original_config
        m_mod.combined_coverage = __import__(
            'pycrunch.session.combined_coverage', fromlist=['combined_coverage']
        ).combined_coverage
        fm_mod.test_map = __import__(
            'pycrunch.session.file_map', fromlist=['test_map']
        ).test_map
