from unittest import mock
from unittest.mock import mock_open, call

from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.session.configuration import Configuration
from pycrunch.session.state import engine
from pycrunch.shared.models import TestState, AllTests
from pycrunch.shared.primitives import TestMetadata


def test_pinned_test_should_change_status():
    sut = AllTests()
    fqn = 'module:test'
    state = TestState(TestMetadata('dummy', 'dummy', 'dummy', fqn, 'pending'), ExecutionResult(), False)
    sut.test_discovered(fqn, state, False)
    single_test = sut.tests.get(fqn, None)
    assert single_test.pinned == False
    sut.pin_test(fqn)
    single_test = sut.tests.get(fqn, None)
    assert single_test.pinned == True



read_data = '''
discovery:
  exclusions:
   - directory_1
   - directory_2
engine:
  runtime: simple
  mode: manual
'''
def test_pin_test_in_engine_should_store_configuration():
    sut = Configuration()
    with mock.patch('io.open', mock_open(read_data=read_data)) as mock_file:
        mock_write = mock_open()
        mock_write.return_value.write = None
        mock_file.side_effect =[
            mock_open(read_data=read_data).return_value,
            mock_open(mock_write).return_value
        ]

        sut.save_pinned_tests_config(['a', 'b'])
        mock_write.assert_has_calls([call().write("pinned-tests"),])



read_data_with_pinned = '''
discovery:
  exclusions:
   - directory_1
   - directory_2
engine:
  runtime: simple
  mode: manual
pinned-tests:
  - a:fqn
  - b
'''
def test_should_load_pinned_tests_from_configuration_on_startup():
    sut = Configuration()
    with mock.patch('io.open', mock_open(read_data=read_data_with_pinned)) as mock_file:
        sut.load_runtime_configuration()
        assert 'a:fqn' in sut.pinned_tests
        assert 'b' in sut.pinned_tests
        assert 'c' not in sut.pinned_tests
