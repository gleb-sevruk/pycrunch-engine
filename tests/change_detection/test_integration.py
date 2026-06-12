"""
T-INT: Integration tests for _smart_execution_plan.
We call _smart_execution_plan directly after wiring up the module-level singletons by hand.
"""

import asyncio
from pathlib import Path

import pytest

from pycrunch.change_detection import normalize_path
from pycrunch.change_detection.import_graph import ImportGraph
from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
from pycrunch.change_detection.fingerprint import fingerprint_source
from pycrunch.session.combined_coverage import CombinedCoverage
from pycrunch.session.file_map import TestMap


def patch_singletons(cache, graph, coverage, tmap):
    """Patch the module-level aliases used inside file_modification_task."""
    import pycrunch.pipeline.file_modification_task as fmt_mod

    fmt_mod._sc_mod.snapshot_cache = cache
    fmt_mod._ig_mod.import_graph = graph
    fmt_mod._cc_mod.combined_coverage = coverage
    fmt_mod._fm_mod.test_map = tmap


def make_task(filepath, cache, graph, coverage, tmap):
    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask

    patch_singletons(cache, graph, coverage, tmap)
    return FileModifiedNotificationTask(filepath)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── T-INT-1: BodyOnlyChange -> only tests for changed function ────────────────


def test_body_only_change_selects_correct_tests(tmp_path):
    src_v1 = (
        "def foo():\n"  # line 1
        "    return 1\n"  # line 2
        "\n"
        "def bar():\n"  # line 4
        "    return 2\n"  # line 5
    )
    src_v2 = (
        "def foo():\n"
        "    return 99\n"  # body changed
        "\n"
        "def bar():\n"
        "    return 2\n"  # unchanged
    )
    filepath = str(tmp_path / 'mod.py')
    (tmp_path / 'mod.py').write_text(src_v2)

    cache = FileSnapshotCache()
    old_fp = fingerprint_source(src_v1, filepath)
    cache.update(filepath, old_fp)

    coverage = CombinedCoverage()
    coverage.ensure_file_statistics_exist(normalize_path(filepath))
    stats = coverage.files[normalize_path(filepath)]
    stats.lines_with_entrypoints[1].add('mod:test_foo')
    stats.lines_with_entrypoints[2].add('mod:test_foo')
    stats.lines_with_entrypoints[4].add('mod:test_bar')
    stats.lines_with_entrypoints[5].add('mod:test_bar')

    tmap = TestMap()
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))

    assert 'mod:test_foo' in plan
    assert 'mod:test_bar' not in plan


# ── T-INT-2: ModuleLevelChange -> transitive importers included ───────────────


def test_module_level_change_includes_importers(tmp_path):
    settings_file = tmp_path / 'settings.py'
    consumer_file = tmp_path / 'consumer.py'

    settings_src_v1 = "TIMEOUT = 5\n"
    settings_src_v2 = "TIMEOUT = 10\n"
    settings_file.write_text(settings_src_v2)

    cache = FileSnapshotCache()
    old_fp = fingerprint_source(settings_src_v1, str(settings_file))
    cache.update(str(settings_file), old_fp)

    coverage = CombinedCoverage()
    norm_consumer = normalize_path(str(consumer_file))
    coverage.dependencies[norm_consumer].add('consumer:test_timeout')

    tmap = TestMap()
    graph = ImportGraph(root=str(tmp_path))
    consumer_fp = fingerprint_source(
        'import settings\n', str(consumer_file), str(tmp_path)
    )
    graph.update_file(str(settings_file), old_fp)
    graph.update_file(str(consumer_file), consumer_fp)

    task = make_task(str(settings_file), cache, graph, coverage, tmap)
    plan = run(task._smart_execution_plan(set()))

    assert 'consumer:test_timeout' in plan


# ── T-INT-3: NoChange -> empty plan, snapshot updated ─────────────────────────


def test_no_change_empty_plan_snapshot_updated(tmp_path):
    src = "def foo():\n    return 1\n"
    filepath = str(tmp_path / 'mod.py')
    (tmp_path / 'mod.py').write_text(src)

    cache = FileSnapshotCache()
    old_fp = fingerprint_source(src, filepath)
    cache.update(filepath, old_fp)

    coverage = CombinedCoverage()
    tmap = TestMap()
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))
    assert plan == set()
    assert cache.get(filepath) is not None


# ── T-INT-4: conftest.py -> all tests in subtree ──────────────────────────────


def test_conftest_includes_subtree_tests(tmp_path):
    conftest = tmp_path / 'conftest.py'
    conftest.write_text('# conftest\n')

    test_in_dir = str(tmp_path / 'test_something.py')
    test_outside = str(tmp_path.parent / 'test_other.py')

    tmap = TestMap()
    tmap.map[test_in_dir] = {'pkg:test_inside'}
    tmap.map[test_outside] = {'pkg:test_outside'}

    cache = FileSnapshotCache()
    coverage = CombinedCoverage()
    graph = ImportGraph()

    task = make_task(str(conftest), cache, graph, coverage, tmap)
    plan = run(task._smart_execution_plan(set()))

    assert 'pkg:test_inside' in plan
    assert 'pkg:test_outside' not in plan


# ── T-INT-5: legacy mode -> plan == dependencies[file] ───────────────────────


def test_legacy_mode_uses_dependencies(tmp_path):
    filepath = str(tmp_path / 'mod.py')
    (tmp_path / 'mod.py').write_text('x = 1\n')

    coverage = CombinedCoverage()
    coverage.dependencies[filepath].add('mod:test_a')
    coverage.dependencies[filepath].add('mod:test_b')

    tmap = TestMap()
    cache = FileSnapshotCache()
    graph = ImportGraph()

    from pycrunch.pipeline.file_modification_task import FileModifiedNotificationTask

    patch_singletons(cache, graph, coverage, tmap)
    task = FileModifiedNotificationTask(filepath)

    plan = task._legacy_fallback()
    assert 'mod:test_a' in plan
    assert 'mod:test_b' in plan


# ── T-INT-6: no coverage data -> legacy fallback ─────────────────────────────


def test_no_coverage_data_falls_back_to_legacy(tmp_path):
    src_v1 = "def foo():\n    return 1\n"
    src_v2 = "def foo():\n    return 99\n"
    filepath = str(tmp_path / 'mod.py')
    (tmp_path / 'mod.py').write_text(src_v2)

    cache = FileSnapshotCache()
    old_fp = fingerprint_source(src_v1, filepath)
    cache.update(filepath, old_fp)

    coverage = CombinedCoverage()
    coverage.dependencies[normalize_path(filepath)].add('mod:test_foo')

    tmap = TestMap()
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))
    assert 'mod:test_foo' in plan
