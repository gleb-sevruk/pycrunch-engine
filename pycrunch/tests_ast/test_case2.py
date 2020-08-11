import unittest

# Notice that currently, coverage marker hit is drawn only for test 1
#   which is not correct - this state is used in BOTH tests
shared_state = 42

class TestWithSharedVariable(unittest.TestCase):
    def test_1(self):
        print(shared_state + 2)

    def test_2(self):
        print(shared_state + 22)

    def test_3(self):
        print('this test should not run if shared state changes')
        # because it is not used here
