import json
import os
import sys
from datetime import datetime
from pprint import pprint

import pytest

from pycrunch.plugins.pytest_support.hot_reload import unload_candidates


def test_pytest_support():
    class Plugin:
        def __init__(self):
            self.passed_tests = set()

        def pytest_runtest_setup(item):
            # called for running each test in 'a' directory
            print("setting up", item)

        def pytest_runtest_logstart(nodeid, location):
            """
                :param str nodeid: full id of the item
                :param location: a triple of ``(filename, linenum, testname)``
            """
            print(f"pytest_runtest_logstart {location}", nodeid)

        def pytest_runtest_logfinish(nodeid, location):
            """ signal the complete finish of running a single test item.

            This hook will be called **after** :func:`pytest_runtest_setup`, :func:`pytest_runtest_call` and
            :func:`pytest_runtest_teardown` hooks.

            :param str nodeid: full id of the item
            :param location: a triple of ``(filename, linenum, testname)``
            """
            print(f"pytest_runtest_logfinish {location}", nodeid)

        def pytest_exception_interact(node, call, report):
            """called when an exception was raised which can potentially be
            interactively handled.

            This hook is only called if an exception was raised
            that is not an internal exception like ``skip.Exception``.
            """
            print(f"pytest_exception_interact {call}")
            pprint(vars(report))
            pass

        def pytest_runtest_logreport(self, report):
            pprint(vars(report))
            if report.when == 'setup':
                pass
            if report.when == 'teardown':
                pass

            if report.when == 'call':
                pass
            if not report.passed:
                # print(report.nodeid)

                # pprint(vars(report))
                self.passed_tests.add(report.nodeid)
                # pprint(report.longreprtext)

    fqn_test_to_run = 'tests_two.py::test_x'
    plugin = Plugin(tests_to_run=[fqn_test_to_run])
    modules_before = set(sys.modules)
    # pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
    # q - quite
    # s - do not capture console logs
    pytest.main([fqn_test_to_run, '-qs'], plugins=[plugin])

    # maybe context manager ?
    modules_after = set(sys.modules)
    difference = set(set(modules_after)).difference(set(modules_before))
    modules_for_unload = unload_candidates(difference)
    for m in modules_for_unload:
        del sys.modules[m]

    print(os.getpid())
    pprint(plugin.passed_tests)
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
    assert 1 == 2


def test_999():
    print('test_method 2')

