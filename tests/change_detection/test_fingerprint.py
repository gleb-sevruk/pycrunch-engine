import pytest

from pycrunch.change_detection.fingerprint import fingerprint_source

FILENAME = '/project/pkg/mod.py'


def fp(source, filename=FILENAME, root=None):
    return fingerprint_source(source, filename, root)


# T-FP-1: same source twice -> identical fingerprint
def test_identical_source_twice():
    src = "def foo():\n    return 1\n"
    assert fp(src) == fp(src)


# T-FP-2: changing function body -> only that body_hash changes, module_level_hash stays
def test_body_change_only_affects_body_hash():
    src1 = "def foo():\n    return 1\n"
    src2 = "def foo():\n    return 2\n"
    f1 = fp(src1)
    f2 = fp(src2)
    assert f1.functions['foo'].body_hash != f2.functions['foo'].body_hash
    assert f1.module_level_hash == f2.module_level_hash


# T-FP-3: changing docstring/comment/blank lines -> all hashes unchanged
def test_docstring_comment_change_no_hash_change():
    src1 = "def foo():\n    return 1\n"
    src2 = 'def foo():\n    """docstring"""\n    return 1\n'
    src3 = "def foo():\n    # a comment\n    return 1\n"
    f1 = fp(src1)
    f2 = fp(src2)
    f3 = fp(src3)
    assert f1.functions['foo'].body_hash == f2.functions['foo'].body_hash
    assert f1.functions['foo'].body_hash == f3.functions['foo'].body_hash
    assert f1.module_level_hash == f2.module_level_hash


# T-FP-4: changing default argument -> module_level_hash changes, body_hash unchanged
def test_default_arg_change_affects_module_level():
    src1 = "def foo(x=1):\n    return x\n"
    src2 = "def foo(x=2):\n    return x\n"
    f1 = fp(src1)
    f2 = fp(src2)
    assert f1.module_level_hash != f2.module_level_hash
    assert f1.functions['foo'].body_hash == f2.functions['foo'].body_hash


# T-FP-5: changing decorator -> module_level_hash changes
def test_decorator_change_affects_module_level():
    src1 = "def foo():\n    return 1\n"
    src2 = "@staticmethod\ndef foo():\n    return 1\n"
    f1 = fp(src1)
    f2 = fp(src2)
    assert f1.module_level_hash != f2.module_level_hash


# T-FP-6: class method qualname and line range includes decorator
def test_class_method_qualname_and_line_range():
    src = "class MyClass:\n    @property\n    def bar(self):\n        return 42\n"
    f = fp(src)
    assert 'MyClass.bar' in f.functions
    fn = f.functions['MyClass.bar']
    assert fn.line_start == 2  # decorator line
    assert fn.line_end == 4
    assert fn.has_decorators is True


# T-FP-7: import_targets collection
def test_import_targets_from_various_forms():
    src = "import x.y\nfrom a.b import c\ndef foo():\n    import inside\n"
    f = fp(src)
    assert 'x.y' in f.import_targets
    assert 'a.b' in f.import_targets
    assert 'a.b.c' in f.import_targets
    assert 'inside' in f.import_targets


# T-FP-8: relative import resolution
def test_relative_import_resolved():
    src = "from . import sibling\n"
    # file is pkg/mod.py, root contains pkg/
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as root:
        pkg = os.path.join(root, 'pkg')
        os.makedirs(pkg)
        filename = os.path.join(pkg, 'mod.py')
        f = fingerprint_source(src, filename, root)
        assert 'pkg.sibling' in f.import_targets


# T-FP-9: SyntaxError propagates
def test_syntax_error_propagates():
    with pytest.raises(SyntaxError):
        fp("def foo(\n")


# T-FP-10: nested function change affects parent body_hash, no separate fingerprint
def test_nested_function_no_separate_fingerprint():
    src1 = "def outer():\n    def inner():\n        return 1\n    return inner()\n"
    src2 = "def outer():\n    def inner():\n        return 99\n    return inner()\n"
    f1 = fp(src1)
    f2 = fp(src2)
    assert 'inner' not in f1.functions
    assert 'outer' in f1.functions
    assert f1.functions['outer'].body_hash != f2.functions['outer'].body_hash
