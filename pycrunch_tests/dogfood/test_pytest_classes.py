import unittest


class MyClass(unittest.TestCase):
    def test_method1(self):
        assert 0 == 0 # fail for demo purposes

    def test_method2(self):
        assert 1 == 1   # fail for demo purposes


class TestForDummies(unittest.TestCase):
    def test_method1(self):
        assert 0 == 0 # fail for demo purposes

    def test_method2(self):
        assert 0 == 0   # fail for demo purposes

    def helper_method(self):
        # should not be in tests
        pass