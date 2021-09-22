from unittest import TestCase

class TestX():
    def test_1(self):
        pass


class SomeClassInhereted(TestCase):
    def test_1(self):
        pass


class AbstractMyTestCase(TestCase):
    pass


class SomeClassDoublyInherited(AbstractMyTestCase):
    def test_1(self):
        pass
