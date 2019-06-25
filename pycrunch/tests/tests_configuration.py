from pycrunch import session


def test_simple_engine_by_default():
    sut = create_sut()
    assert sut.runtime_engine == 'simple'


def test_can_change_to_pytest():
    sut = create_sut()
    sut.runtime_engine_will_change('pytest')
    assert sut.runtime_engine == 'pytest'

def create_sut():
    return session.configuration.Configuration()


def test_non_supported_engine_throws():
    import pytest
    sut = create_sut()
    with pytest.raises(Exception):
        sut.runtime_engine_will_change('not-supported')