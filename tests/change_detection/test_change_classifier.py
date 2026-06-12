from pycrunch.change_detection.change_classifier import (
    BodyOnlyChange,
    ModuleLevelChange,
    NoChange,
    UnparseableChange,
    classify,
)
from pycrunch.change_detection.fingerprint import fingerprint_source

FILENAME = '/project/mod.py'


def fp(source):
    return fingerprint_source(source, FILENAME)


# T-CL-1: identical source -> NoChange
def test_identical_source_no_change():
    src = "def foo():\n    return 1\n"
    old = fp(src)
    kind, new_fp = classify(old, src, FILENAME)
    assert isinstance(kind, NoChange)
    assert new_fp is not None


# T-CL-2: only body change -> BodyOnlyChange with OLD fingerprint (old line ranges)
def test_body_only_change_old_line_ranges():
    src1 = "def foo():\n    return 1\n"
    # insert blank line before foo to shift it down in the new source
    src2 = "\ndef foo():\n    return 99\n"
    old = fp(src1)
    kind, new_fp = classify(old, src2, FILENAME)
    assert isinstance(kind, BodyOnlyChange)
    assert len(kind.changed_functions) == 1
    changed = next(iter(kind.changed_functions))
    # Must return OLD line range (line 1 in src1), not new (line 2 in src2)
    assert changed.line_start == old.functions['foo'].line_start
    assert changed.line_end == old.functions['foo'].line_end


# T-CL-3: two body changes -> both in changed_functions
def test_two_body_changes():
    src1 = "def foo():\n    return 1\ndef bar():\n    return 2\n"
    src2 = "def foo():\n    return 11\ndef bar():\n    return 22\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME)
    assert isinstance(kind, BodyOnlyChange)
    qualnames = {f.qualname for f in kind.changed_functions}
    assert 'foo' in qualnames
    assert 'bar' in qualnames


# T-CL-4: constant change -> ModuleLevelChange
def test_constant_change_module_level():
    src1 = "TIMEOUT = 5\ndef foo():\n    return 1\n"
    src2 = "TIMEOUT = 10\ndef foo():\n    return 1\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME)
    assert isinstance(kind, ModuleLevelChange)


# T-CL-5: old=None -> ModuleLevelChange
def test_no_old_snapshot_is_module_level():
    src = "def foo():\n    return 1\n"
    kind, new_fp = classify(None, src, FILENAME)
    assert isinstance(kind, ModuleLevelChange)
    assert new_fp is not None


# T-CL-6: SyntaxError -> UnparseableChange, fp=None
def test_syntax_error_unparseable():
    src1 = "def foo():\n    return 1\n"
    old = fp(src1)
    kind, new_fp = classify(old, "def foo(\n", FILENAME)
    assert isinstance(kind, UnparseableChange)
    assert new_fp is None


# T-CL-7: deleted function (synthetic: equal module_level_hash) -> old fingerprint in changed_functions
def test_deleted_function_in_changed():
    # We need module_level_hash to stay the same but a function to disappear.
    # This is synthetic — in practice deletion changes the skeleton.
    # We achieve it by patching old to contain an extra function not in new.
    from pycrunch.change_detection.fingerprint import (
        FileFingerprint,
        FunctionFingerprint,
    )

    src = "def foo():\n    return 1\n"
    real_fp = fp(src)
    ghost = FunctionFingerprint(
        qualname='ghost',
        body_hash='abc',
        line_start=10,
        line_end=12,
        has_decorators=False,
    )
    old = FileFingerprint(
        functions={**real_fp.functions, 'ghost': ghost},
        module_level_hash=real_fp.module_level_hash,
        import_targets=real_fp.import_targets,
    )
    kind, _ = classify(old, src, FILENAME)
    assert isinstance(kind, BodyOnlyChange)
    qualnames = {f.qualname for f in kind.changed_functions}
    assert 'ghost' in qualnames


# T-CL-8: only comments/docstrings changed -> NoChange
def test_only_comments_no_change():
    src1 = "def foo():\n    return 1\n"
    src2 = "def foo():\n    # a comment\n    return 1\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME)
    assert isinstance(kind, NoChange)


# T-CL-9: reordering two top-level functions -> ModuleLevelChange (documented behavior)
def test_reorder_functions_is_module_level():
    src1 = "def foo():\n    return 1\ndef bar():\n    return 2\n"
    src2 = "def bar():\n    return 2\ndef foo():\n    return 1\n"
    old = fp(src1)
    kind, _ = classify(old, src2, FILENAME)
    assert isinstance(kind, ModuleLevelChange)
