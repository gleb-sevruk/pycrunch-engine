from pprint import pprint
from unittest import mock

from pycrunch.session.diagnostics import diagnostic_engine

def test_modules():
    actual = diagnostic_engine.get_modules()
    pprint(actual)

def test_diagnostic_env():
    with mock.patch('os.environ', {'test': 'var'}):
        env = dict(diagnostic_engine.get_env())
        assert env['test'] == 'var'

def test_summary():
    actual = diagnostic_engine.summary()
    pprint(actual)
    assert 'modules' in actual
    assert 'env' in actual