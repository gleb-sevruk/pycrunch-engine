from pathlib import Path

from pycrunch.discovery.ast_discovery import AstTestDiscovery
from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.insights import trace
from pycrunch.session.configuration import Configuration

def test_regular_classes_not_discovered():
    test_names = run_ast_dogfood_discovery()
    assert 'NotTestClass::test_one' not in test_names


def test_classes_with_ending_patters_not_returned():
    test_names = run_ast_dogfood_discovery()
    assert 'AnotherTest::test_another' not in test_names


def test_classes_inherited_directly_from_test_case():
    test_names = run_ast_dogfood_discovery()
    assert 'InheritedFromBase::test_with_base_class' in test_names

def test_classes_inherited_non_directly_from_test_case():
    test_names = run_ast_dogfood_discovery()
    # trace(test_names.__code__)
    assert 'AdvancedScenario::test_advanced' in test_names

#
# def test_classes_with_unit_tests_are_discoverable():
#     actual = run_ast_dogfood_discovery()
#     test_names = list(map(lambda _: _.name, actual.tests))
#     assert len(test_names) > 0
#     assert 'MyClass::test_method1' in test_names
#     assert 'MyClass::test_method2' in test_names
#     assert 'TestForDummies::test_method1' in test_names
#     assert 'TestForDummies::test_method2' in test_names
#     assert 'TestForDummies::helper_method' not in test_names
#


def run_ast_dogfood_discovery():
    root_folder = Path('.')
    current_folder = root_folder.joinpath('pycrunch', 'tests', 'dogfood_ast').absolute()
    sut = AstTestDiscovery(str(root_folder.absolute()), Configuration())
    actual = sut.find_tests_in_folder(str(current_folder.absolute()))
    return list(map(lambda _: _.name, actual.tests))

