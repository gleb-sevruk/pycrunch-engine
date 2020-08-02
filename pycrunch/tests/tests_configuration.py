from _pydecimal import DecimalException
from unittest import mock
from unittest.mock import mock_open, patch, Mock

import pytest

from pycrunch import session


def test_django_engine_by_default():
    sut = create_sut()
    assert sut.runtime_engine == 'django'


def test_can_change_to_simple_engine():
    sut = create_sut()
    sut.runtime_engine_will_change('simple')
    assert sut.runtime_engine == 'simple'


def test_can_change_to_django_engine():
    sut = create_sut()
    sut.runtime_engine_will_change('django')
    assert sut.runtime_engine == 'django'


def create_sut():
    return session.configuration.Configuration()

def test_should_call_auto_config():
    with patch('pycrunch.session.configuration.AutoConfiguration.ensure_configuration_exist') as auto:
        sut = create_sut()
        sut.load_runtime_configuration()
        auto.assert_called_once()

def test_non_supported_engine_throws():
    import pytest
    sut = create_sut()
    with pytest.raises(Exception):
        sut.runtime_engine_will_change('not-supported')

read_data = '''
engine:
  runtime: simple
  timeout: 42
discovery:
  exclusions:
   - directory_1
   - directory_2
mode: manual

'''
def test_exclusion_list():
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert 'directory_1' in sut.discovery_exclusions
        assert 'directory_2' in sut.discovery_exclusions
        assert 'directory_3' not in sut.discovery_exclusions

def test_engine_mode_auto_by_default():
    sut = create_sut()
    assert sut.engine_mode == 'auto'

def test_unsupported_engine_mode_raises_exception():
    sut = create_sut()
    with pytest.raises(Exception):
        sut.runtime_mode_will_change('no-way')

def test_runtime_engine_from_config():
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert sut.runtime_engine == 'simple'

def test_timeout_is_1min_by_default():
    sut = create_sut()
    assert sut.execution_timeout_in_seconds == 60

def test_timeout_is_none_when_zero():
    # this will force task to wait forever
    sut = create_sut()
    sut.execution_timeout_in_seconds = 0
    assert sut.get_execution_timeout() is None

def test_timeout_is_taken_from_config():
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()

        assert sut.execution_timeout_in_seconds == 42

def test_environment_vars():
    read_data = '''
    discovery:
      exclusions:
       - directory_1
       - directory_2
    engine:
      runtime: simple
      mode: manual
    env:
      DJANGO_SETTINGS: insuredportal.settings
      ENV2: test
    '''

    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert 'insuredportal.settings' == sut.environment_vars.get('DJANGO_SETTINGS')
        assert 'test' == sut.environment_vars.get('ENV2')
        assert sut.environment_vars.get('NOT') == None



def test_path_map_config_read():
    read_data = '''
    discovery:
      exclusions:
       - directory_1
       - directory_2
    engine:
      runtime: simple
      mode: manual
    env:
      DJANGO_SETTINGS: insuredportal.settings
      ENV2: test
    path-mapping:
      /code: /localfs/easyproject 
    '''

    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert '/code' == sut.path_mapping.path_in_container
        assert '/localfs/easyproject' == sut.path_mapping.path_on_local_ide



def test_cpu_cores_considered():
    read_data = '''
    discovery:
      exclusions:
       - directory_1
       - directory_2
    engine:
      runtime: simple
      cpu-cores: 42
    '''

    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert sut.cpu_cores == 42

def test_cpu_cores_by_default_no_more_than_4():
    with mock.patch('pycrunch.session.configuration.multiprocessing') as multiprocessing_mock:
        # lets just use 4 by default to not burn machine
        multiprocessing_mock.cpu_count.return_value = 16
        sut = create_sut()
        assert sut.cpu_cores == 4


def test_two_cores_use_1_by_default():
    with mock.patch('pycrunch.session.configuration.multiprocessing') as multiprocessing_mock:
        multiprocessing_mock.cpu_count.return_value = 2
        sut = create_sut()
        assert sut.cpu_cores == 1

def test_one_core_use_1_by_default():
    with mock.patch('pycrunch.session.configuration.multiprocessing') as multiprocessing_mock:
        multiprocessing_mock.cpu_count.return_value = 1
        sut = create_sut()
        assert sut.cpu_cores == 1

def test_from_3_to_7_cores_use_half_of_them_by_default():
    with mock.patch('pycrunch.session.configuration.multiprocessing') as multiprocessing_mock:
        # lets just use 4 by default to not burn machine
        multiprocessing_mock.cpu_count.return_value = 6
        sut = create_sut()
        assert sut.cpu_cores == 3


def test_multiprocessing_threshold_considered():
    read_data = '''
    engine:
      runtime: simple
      multiprocessing-threshold: 1
    '''

    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert sut.multiprocessing_threshold == 1


def test_multiprocessing_threshold_by_default_5():
    sut = create_sut()
    # minimum number of tests to schedule per core
    assert sut.multiprocessing_threshold == 5


def test_load_pytest_plugins_false_by_default():
    sut = create_sut()
    assert sut.load_pytest_plugins == False

def test_load_pytest_plugins():
    read_data = '''
engine:
  runtime: simple
  load-pytest-plugins: true
discovery:
  exclusions:
   - directory_1
   - directory_2
mode: manual

'''
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert sut.load_pytest_plugins == True

