import unittest

# This is rather simple test case
# What needs to be done is to calculate ast hash for each method
#   and rerun it when o ne of it changes

class TestWithTwoMethods(unittest.TestCase):
    def test_1(self):
        print('when this changed - only one test should run')

    def test_2(self):
        print('when this changed - test 1 should not run')

    def test_3(self):
        print('when this changed - only one test (3) will run')

