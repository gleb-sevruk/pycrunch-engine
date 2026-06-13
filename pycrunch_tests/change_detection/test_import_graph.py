from pycrunch.change_detection.fingerprint import compute_file_fingerprint
from pycrunch.change_detection.import_graph import ImportGraph


def make_graph(root):
    return ImportGraph(root=str(root))


def make_fp(source, filename, root):
    return compute_file_fingerprint(source, str(filename), str(root))

# T-IG-1: a imports b -> transitive_importers(b) == {a}
def test_direct_importer(tmp_path):
    root = tmp_path
    pkg = root / 'pkg'


    a = root / 'a.py'
    b = root / 'b.py'
    a.write_text('import b\n')
    b.write_text('x = 1\n')

    g = make_graph(root)
    g.update_file(str(a), make_fp('import b\n', a, root))
    g.update_file(str(b), make_fp('x = 1\n', b, root))

    importers = g.transitive_importers(str(b))
    assert str(a.resolve()) in importers


# T-IG-2: a->b->c -> transitive_importers(c) == {a, b}
def test_transitive_importers(tmp_path):
    root = tmp_path
    a = root / 'a.py'
    b = root / 'b.py'
    c = root / 'c.py'

    g = make_graph(root)
    g.update_file(str(a), make_fp('import b\n', a, root))
    g.update_file(str(b), make_fp('import c\n', b, root))
    g.update_file(str(c), make_fp('x = 1\n', c, root))

    importers = g.transitive_importers(str(c))
    assert str(a.resolve()) in importers
    assert str(b.resolve()) in importers


# T-IG-3: cycle a<->b -> terminates, both are mutual importers
def test_cycle_terminates(tmp_path):
    root = tmp_path
    a = root / 'a.py'
    b = root / 'b.py'

    g = make_graph(root)
    g.update_file(str(a), make_fp('import b\n', a, root))
    g.update_file(str(b), make_fp('import a\n', b, root))

    importers_a = g.transitive_importers(str(a))
    importers_b = g.transitive_importers(str(b))
    assert str(b.resolve()) in importers_a
    assert str(a.resolve()) in importers_b


# T-IG-4: update_file after removing import -> edge disappears
def test_update_removes_old_edge(tmp_path):
    root = tmp_path
    a = root / 'a.py'
    b = root / 'b.py'

    g = make_graph(root)
    g.update_file(str(a), make_fp('import b\n', a, root))
    g.update_file(str(b), make_fp('x = 1\n', b, root))

    assert str(a.resolve()) in g.transitive_importers(str(b))

    # now a no longer imports b
    g.update_file(str(a), make_fp('x = 1\n', a, root))
    assert str(a.resolve()) not in g.transitive_importers(str(b))


# T-IG-5: remove_file -> disappears as importer and as target
def test_remove_file(tmp_path):
    root = tmp_path
    a = root / 'a.py'
    b = root / 'b.py'

    g = make_graph(root)
    g.update_file(str(a), make_fp('import b\n', a, root))
    g.update_file(str(b), make_fp('x = 1\n', b, root))

    g.remove_file(str(a))
    assert str(a.resolve()) not in g.transitive_importers(str(b))
    # b's own importers should be empty
    assert g.transitive_importers(str(b)) == set()


# T-IG-6: __init__.py resolves to package name
def test_init_py_resolves_to_package(tmp_path):
    root = tmp_path
    pkg = root / 'pkg'
    pkg.mkdir()
    init = pkg / '__init__.py'
    consumer = root / 'consumer.py'

    g = make_graph(root)
    g.update_file(str(init), make_fp('x = 1\n', init, root))
    g.update_file(str(consumer), make_fp('import pkg\n', consumer, root))

    importers = g.transitive_importers(str(init))
    assert str(consumer.resolve()) in importers
