from pycrunch.session.configuration import PathMapping


def test_path_mapping_ok():
    sut = PathMapping('/code', '/gleb/ba/django')
    actual = sut.map_to_local_fs('/code/main.py')
    assert '/gleb/ba/django/main.py' == actual


def test_path_mapping_nested():
    sut = PathMapping('/code', '/gleb/ba/django')
    actual = sut.map_to_local_fs('/code/core/code/main.py')
    assert '/gleb/ba/django/core/code/main.py' == actual