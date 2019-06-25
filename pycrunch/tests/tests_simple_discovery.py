import os
from pathlib import Path
from pprint import pprint

from pycrunch.discovery.simple import SimpleTestDiscovery


def test_simple_discovery():
    root_folder = '/Users/gleb/code/PyCrunch/'
    current_folder = root_folder + 'pycrunch/tests/'

    sut = SimpleTestDiscovery(root_folder)
    actual = sut.find_tests_in_folder(current_folder)

    found_flag = False
    expected_path = current_folder + 'tests_simple_discovery.py'

    for t in actual.tests:
        if t.filename == expected_path:
            if t.name == 'test_simple_discovery':
                found_flag = True
                break

    assert found_flag

def test_dir_walk():
    for x in Path('/Users/gleb/code/PyCrunch/').glob('**/test*.py'):
        print(x.name)

def test_module_with_tests_simple():
    sut = SimpleTestDiscovery('')
    assert sut.is_module_with_tests('tests_simple')
    assert sut.is_module_with_tests('simple_tests')


def test_module_with_tests_nested():
    sut = SimpleTestDiscovery('')
    assert sut.is_module_with_tests('nested.tests_simple')
    assert sut.is_module_with_tests('nested.even_more.tests_simple')
