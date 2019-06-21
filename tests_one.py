from datetime import datetime
from pprint import pprint

import pytest


def test_pytest_support():
    class Plugin:
        def __init__(self):
            self.passed_tests = set()

        def pytest_runtest_logreport(self, report):
            if not report.passed:
                # print(report.nodeid)

                # pprint(vars(report))
                self.passed_tests.add(report.nodeid)
                # pprint(report.longreprtext)

    plugin = Plugin()

    # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
    pytest.main(['tests_two.py::test_x', '-q'], plugins=[plugin])
    print('testing output interception')


def test_1():
    print('test_method__op 3')
    print('test_method__op 2')
    a = 5 + 6 + 3
    # b = a * 12
    # b = a * 12
    b = a * 12
    # b = a * 12
    print(f'b {b}')
    print('test_method__op 5')

def test_6():
    import playground
    playground.kurlik(10, 23)
    # print('test_method 2')
    print('test_method 2')


def test_999():
    print('test_method 2')

