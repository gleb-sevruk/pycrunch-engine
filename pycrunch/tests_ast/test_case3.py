import unittest

# Notice that currently, coverage marker hit is drawn only for test 1
#   which is not correct - this state is used in BOTH tests
from .some_shared_module import shared_variable, stupid_function
from ..session.state import ExecutionResult


class TestWithSharedModule(unittest.TestCase):
    def test_1(self):
        print(shared_variable + 2)

    def test_2(self):
        print(stupid_function() + 99)

    def test_3(self):
        print('this test should not run if shared state changes')
        # because it is not used here
