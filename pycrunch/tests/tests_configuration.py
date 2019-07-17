from unittest import mock
from unittest.mock import mock_open

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


def test_non_supported_engine_throws():
    import pytest
    sut = create_sut()
    with pytest.raises(Exception):
        sut.runtime_engine_will_change('n-s')

read_data = '''
discovery:
  exclusions:
   - directory_1
   - directory_2
engine:
  runtime: simple
'''
def test_exclusion_list():
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert 'directory_1' in sut.discovery_exclusions
        assert 'directory_2' in sut.discovery_exclusions
        assert 'directory_3' not in sut.discovery_exclusions

def test_runtime_engine_from_config():
    with mock.patch('io.open', mock_open(read_data=read_data)) as x:
        sut = create_sut()
        sut.load_runtime_configuration()
        assert sut.runtime_engine == 'simple'