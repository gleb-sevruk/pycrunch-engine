"""
T-TF: Tests for M7 — smart change detection in test files.

All tests use fingerprint_source(..., test_file=True) for old snapshots so that
the compatibility migration path (old.test_file=False → skeleton_changed=True) is
exercised only in T-TF-12.
"""

import asyncio

from pycrunch.change_detection import match_fqns, normalize_path
from pycrunch.change_detection.change_classifier import (
    NoChange,
    TestFileChange,
    classify,
)
from pycrunch.change_detection.fingerprint import fingerprint_source
from pycrunch.change_detection.import_graph import ImportGraph
from pycrunch.change_detection.snapshot_cache import FileSnapshotCache
from pycrunch.session.combined_coverage import CombinedCoverage
from pycrunch.session.file_map import TestMap

FILENAME = '/project/tests/test_mod.py'


def fp(source, test_file=True):
    return fingerprint_source(source, FILENAME, test_file=test_file)


# ── helpers for integration tests ────────────────────────────────────────────


def patch_singletons(cache, graph, coverage, tmap):
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


# ── T-TF-1: body of one test changed → only that test ────────────────────────


def test_body_change_schedules_only_changed_test():
    src1 = "def test_a():\n    assert 1 == 1\n\ndef test_b():\n    assert 2 == 2\n"
    src2 = (
        "def test_a():\n"
        "    assert 1 == 99\n"  # body changed
        "\n"
        "def test_b():\n"
        "    assert 2 == 2\n"  # unchanged
    )
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.changed_tests == frozenset({'test_a'})
    assert kind.changed_fixtures == frozenset()
    assert not kind.skeleton_changed


# ── T-TF-2: parametrize case added → skeleton unchanged, only test_a ─────────


def test_parametrize_change_does_not_affect_skeleton():
    src1 = (
        "@pytest.mark.parametrize('x', [1, 2])\n"
        "def test_a(x):\n"
        "    assert x > 0\n"
        "\n"
        "def test_b():\n"
        "    assert True\n"
    )
    src2 = (
        "@pytest.mark.parametrize('x', [1, 2, 3])\n"  # added case
        "def test_a(x):\n"
        "    assert x > 0\n"
        "\n"
        "def test_b():\n"
        "    assert True\n"
    )
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.changed_tests == frozenset({'test_a'})
    assert not kind.skeleton_changed


# ── T-TF-3: @skip added → skeleton unchanged, only test_a ────────────────────


def test_skip_decorator_added_does_not_affect_skeleton():
    src1 = "def test_a():\n    assert True\n\ndef test_b():\n    assert True\n"
    src2 = "@pytest.mark.skip\ndef test_a():\n    assert True\n\ndef test_b():\n    assert True\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.changed_tests == frozenset({'test_a'})
    assert not kind.skeleton_changed


# ── T-TF-4: fixture body changed → changed_fixtures, skeleton unchanged ──────


def test_fixture_body_change_goes_to_changed_fixtures():
    src1 = "@pytest.fixture\ndef db():\n    return {}\n"
    src2 = "@pytest.fixture\ndef db():\n    return {'key': 'val'}\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.changed_fixtures == frozenset({'db'})
    assert kind.changed_tests == frozenset()
    assert not kind.skeleton_changed


# ── T-TF-5: fixture scope changed → changed_fixtures, skeleton unchanged ─────


def test_fixture_scope_change_does_not_affect_skeleton():
    src1 = "@pytest.fixture(scope='session')\ndef db():\n    return {}\n"
    src2 = "@pytest.fixture(scope='function')\ndef db():\n    return {}\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.changed_fixtures == frozenset({'db'})
    assert not kind.skeleton_changed


# ── T-TF-6: import added → skeleton changed → all tests ──────────────────────


def test_import_added_causes_skeleton_change():
    src1 = "def test_a():\n    assert True\n"
    src2 = "import os\ndef test_a():\n    assert True\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.skeleton_changed


# ── T-TF-7: module-level constant changed → skeleton changed ─────────────────


def test_module_constant_change_causes_skeleton_change():
    src1 = "TIMEOUT = 1\ndef test_a():\n    assert True\n"
    src2 = "TIMEOUT = 2\ndef test_a():\n    assert True\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.skeleton_changed


# ── T-TF-8: helper function changed → changed_helpers, coverage-based plan ───


def test_helper_change_uses_coverage_for_plan(tmp_path):
    src1 = (
        "def _helper():\n"  # line 1
        "    return 1\n"  # line 2
        "\n"
        "def test_a():\n"  # line 4
        "    assert _helper()\n"  # line 5
    )
    src2 = (
        "def _helper():\n"
        "    return 99\n"  # body changed
        "\n"
        "def test_a():\n"
        "    assert _helper()\n"
    )
    filepath = str(tmp_path / 'test_mod.py')
    (tmp_path / 'test_mod.py').write_text(src2)

    old = fingerprint_source(src1, filepath, test_file=True)
    cache = FileSnapshotCache()
    cache.update(filepath, old)

    coverage = CombinedCoverage()
    coverage.ensure_file_statistics_exist(normalize_path(filepath))
    stats = coverage.files[normalize_path(filepath)]
    # _helper at lines 1-2 is called by test_a
    stats.lines_with_entrypoints[1].add('test_mod:test_a')
    stats.lines_with_entrypoints[2].add('test_mod:test_a')

    tmap = TestMap()
    tmap.map[filepath] = {'test_mod:test_a'}
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))
    assert 'test_mod:test_a' in plan


# ── T-TF-9: class method in test class → qualname matching ───────────────────


def test_class_method_qualname_matching(tmp_path):
    src1 = (
        "class TestSuite:\n"
        "    def test_foo(self):\n"
        "        assert True\n"
        "    def test_bar(self):\n"
        "        assert True\n"
    )
    src2 = (
        "class TestSuite:\n"
        "    def test_foo(self):\n"
        "        assert False\n"  # body changed
        "    def test_bar(self):\n"
        "        assert True\n"  # unchanged
    )
    filepath = str(tmp_path / 'test_suite.py')
    (tmp_path / 'test_suite.py').write_text(src2)

    old = fingerprint_source(src1, filepath, test_file=True)
    cache = FileSnapshotCache()
    cache.update(filepath, old)

    coverage = CombinedCoverage()
    tmap = TestMap()
    tmap.map[filepath] = {
        'test_suite:TestSuite::test_foo',
        'test_suite:TestSuite::test_bar',
    }
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))
    assert 'test_suite:TestSuite::test_foo' in plan
    assert 'test_suite:TestSuite::test_bar' not in plan


# ── T-TF-10: match_fqns handles parametrized FQN variants ────────────────────


def test_match_fqns_handles_parametrized_variants():
    candidates = {'mod:test_a[1]', 'mod:test_a[2]', 'mod:test_b'}
    result = match_fqns('test_a', candidates)
    assert result == {'mod:test_a[1]', 'mod:test_a[2]'}


# ── T-TF-11: comment-only change → NoChange ───────────────────────────────────


def test_comment_only_change_is_no_change():
    src1 = "def test_a():\n    assert True\n"
    src2 = "def test_a():\n    # comment\n    assert True\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, NoChange)


# ── T-TF-12: old snapshot built without test_file=True → conservative ────────


def test_old_snapshot_without_test_file_flag_is_conservative():
    src1 = "def test_a():\n    assert True\n"
    src2 = "def test_a():\n    assert False\n"
    old = fp(src1, test_file=False)  # old-style snapshot
    kind, _ = classify(old, src2, FILENAME, test_file=True)
    assert isinstance(kind, TestFileChange)
    assert kind.skeleton_changed  # conservative: run everything


# ── T-TF-13: no FQN match for changed_tests → safety fallback ────────────────


def test_no_fqn_match_falls_back_to_all_tests(tmp_path):
    src1 = "def test_a():\n    assert True\n"
    src2 = "def test_a():\n    assert False\n"
    filepath = str(tmp_path / 'test_mod.py')
    (tmp_path / 'test_mod.py').write_text(src2)

    old = fingerprint_source(src1, filepath, test_file=True)
    cache = FileSnapshotCache()
    cache.update(filepath, old)

    coverage = CombinedCoverage()
    tmap = TestMap()
    # FQNs don't match the qualname 'test_a' (different naming convention)
    tmap.map[filepath] = {'test_mod:SPEC_a', 'test_mod:SPEC_b'}
    graph = ImportGraph()
    task = make_task(filepath, cache, graph, coverage, tmap)

    plan = run(task._smart_execution_plan(set()))
    # Safety fallback: all tests in file
    assert 'test_mod:SPEC_a' in plan
    assert 'test_mod:SPEC_b' in plan


# ── T-TF-14: non-test file is unaffected by test_file logic ──────────────────


def test_non_test_file_still_uses_body_only_change():
    src1 = "@decorator\ndef foo():\n    return 1\n"
    src2 = "@decorator\n@another\ndef foo():\n    return 1\n"
    # Non-test file: decorator added → affects module_level_hash for non-test files
    f1 = fingerprint_source(src1, '/project/src/utils.py', test_file=False)
    f2 = fingerprint_source(src2, '/project/src/utils.py', test_file=False)
    # Decorator change in non-test file changes skeleton
    assert f1.module_level_hash != f2.module_level_hash

    # Same file with test_file=True: foo() is not a test (name doesn't start with test_)
    # So decorator is NOT stripped → skeleton still changes
    f3 = fingerprint_source(src1, '/project/tests/test_mod.py', test_file=True)
    f4 = fingerprint_source(src2, '/project/tests/test_mod.py', test_file=True)
    assert f3.module_level_hash != f4.module_level_hash
