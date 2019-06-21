from pprint import pprint

import pytest


class Plugin:
    def __init__(self):
        self.passed_tests = set()
    def pytest_runtest_logreport(self, report):
        # if report.passed:
        print(report.nodeid)

        pprint(vars(report))
        self.passed_tests.add(report.nodeid)
        pprint(report.longreprtext)


plugin = Plugin()

# pytest.main(['tests_two.py::test_x', '-p', 'no:terminal'])
pytest.main(['tests_two.py::test_x'], plugins=[plugin])
