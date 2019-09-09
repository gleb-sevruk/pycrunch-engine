import io
import os
from pathlib import Path
from pprint import pprint
from unittest import mock
from unittest.mock import mock_open, create_autospec

from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.session.configuration import Configuration


def test_simple_discovery():
    actual = run_dogfood_discovery()

    found_flag = False
    for t in actual.tests:
        if t.filename.endswith('test_discovery_specs_demo.py'):
            if t.name == 'test_regular':
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
    assert sut.is_module_with_tests('api_tests.tests')
    assert sut.is_module_with_tests('nested.even_more.tests_simple')


def test_only_methods_are_discovered_not_variables():
    actual = run_dogfood_discovery()
    test_names = list(map(lambda _: _.name, actual.tests))
    assert len(test_names) > 0
    assert 'test_variable' not in test_names

def test_classes_with_unit_tests_are_discoverable():
    actual = run_dogfood_discovery()
    test_names = list(map(lambda _: _.name, actual.tests))
    assert len(test_names) > 0
    assert 'MyClass::test_method1' in test_names
    assert 'MyClass::test_method2' in test_names
    assert 'TestForDummies::test_method1' in test_names
    assert 'TestForDummies::test_method2' in test_names
    assert 'TestForDummies::helper_method' not in test_names


def run_dogfood_discovery():
    root_folder = Path('.')
    current_folder = root_folder.joinpath('pycrunch', 'tests', 'dogfood').absolute()
    sut = SimpleTestDiscovery(str(root_folder.absolute()), Configuration())
    actual = sut.find_tests_in_folder(str(current_folder.absolute()))
    return actual


