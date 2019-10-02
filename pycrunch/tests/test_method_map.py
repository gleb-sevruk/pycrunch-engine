import unittest
from pycrunch.session.method_map import FilesMethodMap, MethodDefinition, MethodMapForSingleFile


def test_affected_single_method():
    sut = FilesMethodMap()
    method_d = MethodDefinition('demo', 2, 4)
    filename = 'fake.py'
    single_file = MethodMapForSingleFile(filename)
    single_file.methods[method_d.name] = method_d

    sut.methods_by_file[filename] = single_file
    assert len(sut.methods_by_file[filename].methods) == 1

    actual = sut.get_affected_methods(filename, [1,2,3,4])
    assert len(actual) == 1
    assert actual[0] == 'demo'



def test_affected_multiple_methods():
    filename = 'fake.py'
    sut = FilesMethodMap()
    single_file = MethodMapForSingleFile(filename)

    method_a = MethodDefinition('demo_first', 2, 4)
    method_b = MethodDefinition('demo_second', 6, 9)
    method_c = MethodDefinition('demo_third', 11, 13)
    single_file.methods[method_a.name] = method_a
    single_file.methods[method_b.name] = method_b
    single_file.methods[method_c.name] = method_c

    sut.methods_by_file[filename] = single_file
    assert len(sut.methods_by_file[filename].methods) == 3
    actual = sut.get_affected_methods(filename, [1,2,3,4, 11,12,12])
    assert actual == ['demo_first', 'demo_third']

def test_snapshot():
    # should return last modified methods
    snapshot_before = FilesMethodMap()
    method_d = MethodDefinition('demo', 2, 4)
    filename = 'fake.py'
    single_file = MethodMapForSingleFile(filename)
    single_file.methods[method_d.name] = method_d


    single_file_after = MethodMapForSingleFile(filename)
    method_after = MethodDefinition('demo', 2, 5)
    single_file_after.methods[method_after.name] = method_after

    # list of methods
    actual = single_file.compare_with_snapshot(single_file_after)
    assert len(actual) == 1
    assert actual[0] == 'demo'

    pass