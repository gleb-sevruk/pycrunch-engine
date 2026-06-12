"""
T-ER: Tests for M9.5 — empty execution plan must not spawn processes.
"""
import asyncio
from unittest.mock import patch, MagicMock

import pytest

from pycrunch.pipeline.run_debouncing import RunDebouncer


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_debouncer(delay: float = 0.001) -> RunDebouncer:
    d = RunDebouncer(debounce_delay=delay)
    d.reset_deadline()  # initialise ts_target so execute_with_delay can sleep
    return d


def _fake_test_state(name='test_a'):
    m = MagicMock()
    m.discovered_test.fqn = f'test_mod:{name}'
    m.discovered_test.filename = 'test_mod.py'
    m.discovered_test.name = name
    m.discovered_test.module = 'test_mod'
    return m


# ── T-ER-1: execute_with_delay with empty dirty_tests → add_task NOT called,
#            run_pending == False, run_timer is None after exit

def test_execute_with_delay_empty_skips_add_task():
    debouncer = _make_debouncer()
    # dirty_tests stays empty; run_pending stays False (we set it manually to
    # simulate being inside schedule_run path)
    debouncer.run_pending = True

    with patch('pycrunch.pipeline.run_debouncing.execution_pipeline') as mock_pipeline:
        run(debouncer.execute_with_delay())
        mock_pipeline.add_task.assert_not_called()

    assert debouncer.run_pending is False
    assert debouncer.run_timer is None


# ── T-ER-2: execute_with_delay with non-empty list → add_task called once with copy

def test_execute_with_delay_nonempty_calls_add_task():
    debouncer = _make_debouncer()
    t = _fake_test_state()
    debouncer.dirty_tests = [t]
    debouncer.run_pending = True

    with patch('pycrunch.pipeline.run_debouncing.execution_pipeline') as mock_pipeline:
        run(debouncer.execute_with_delay())
        mock_pipeline.add_task.assert_called_once()

    assert debouncer.run_pending is False
    assert debouncer.run_timer is None
    assert debouncer.dirty_tests == []


# ── T-ER-3: empty pass → then real test added → debouncer not jammed

def test_debouncer_not_jammed_after_empty_skip():
    debouncer = _make_debouncer()

    # First cycle: empty → execute_with_delay fires, skips, resets state
    with patch('pycrunch.pipeline.run_debouncing.execution_pipeline'):
        run(debouncer.execute_with_delay())

    assert debouncer.run_pending is False

    # Second cycle: real test added + schedule_run
    t = _fake_test_state()
    debouncer.add_tests([t])

    called = []
    with patch('pycrunch.pipeline.run_debouncing.execution_pipeline') as mock_pipeline:
        mock_pipeline.tasks_in_queue.return_value = 0
        # Manually drive schedule_run + execute_with_delay (skipping asyncio timer)
        debouncer.run_pending = False
        debouncer.dirty_tests = [t]
        run(debouncer.execute_with_delay())
        called.append(mock_pipeline.add_task.call_count)

    assert called[0] == 1, 'RunTestTask must be created after a non-empty second pass'


# ── T-ER-4: RunTestTask([]).run() returns without spawning processes

def test_run_test_task_empty_returns_early():
    from pycrunch.pipeline.run_test_task import RunTestTask, RemoteDebugParams

    task = RunTestTask([], RemoteDebugParams.disabled())

    with patch('pycrunch.pipeline.run_test_task.MultiprocessTestRunner') as mock_runner_cls:
        run(task.run())
        mock_runner_cls.assert_not_called()


# ── T-ER-5: Integration smart NoChange → add_tests not called, coverage-push sent

def test_smart_no_change_does_not_call_add_tests(tmp_path):
    from pycrunch.change_detection import normalize_path
    from pycrunch.change_detection.fingerprint import fingerprint_source
    from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
    from pycrunch.change_detection.import_graph import ImportGraph
    from pycrunch.session.file_map import TestMap
    from pycrunch.session.combined_coverage import CombinedCoverage
    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask
    from pycrunch.shared.models import AllTests
    from pycrunch.discovery.simple import DiscoveredTest

    src = "def test_a():\n    assert True\n"
    filepath = str(tmp_path / 'test_mod.py')
    (tmp_path / 'test_mod.py').write_text(src)  # identical → NoChange

    fqn_a = 'test_mod:test_a'
    cache = FileSnapshotCache()
    old_fp = fingerprint_source(src, filepath, test_file=True)
    cache.update(filepath, old_fp, src)

    coverage = CombinedCoverage()
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
    # Re-seed coverage after test_discovered wiped it
    coverage.ensure_file_statistics_exist(normalize_path(filepath))
    coverage.files[normalize_path(filepath)].lines_with_entrypoints[1] = {fqn_a}

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
        async def test_discovery_will_become_available(self, test_set, preserve_state=False):
            pass

    state_mod.engine = FakeEngine()
    state_mod.config = FakeConfig()

    push_calls = []

    async def fake_push(pipe_arg, all_tests_arg):
        push_calls.append(1)

    add_tests_calls = []
    original_add_tests = fmt_mod.run_debouncer.add_tests

    def spy_add_tests(tests):
        add_tests_calls.append(len(tests))
        return original_add_tests(tests)

    fmt_mod.run_debouncer.add_tests = spy_add_tests

    try:
        with patch.object(fmt_mod._cc_mod, 'push_combined_coverage_updated', fake_push):
            run(FileModifiedNotificationTask(filepath)._smart_execution_plan(set(), old_fp))

        # add_tests must NOT have been called (level-1 guard fires first)
        assert add_tests_calls == [], f'add_tests was called unexpectedly: {add_tests_calls}'
        # push must have been sent
        assert len(push_calls) > 0, 'coverage push was not sent'
    finally:
        state_mod.engine = original_engine
        state_mod.config = original_config
        fmt_mod.run_debouncer.add_tests = original_add_tests
        m_mod.combined_coverage = __import__(
            'pycrunch.session.combined_coverage', fromlist=['combined_coverage']
        ).combined_coverage
        fm_mod.test_map = __import__(
            'pycrunch.session.file_map', fromlist=['test_map']
        ).test_map
