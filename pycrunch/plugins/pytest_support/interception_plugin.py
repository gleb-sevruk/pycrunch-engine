from pprint import pprint


class PyTestInterceptionPlugin:
    def __init__(self, tests_to_run):
        self.passed_tests = set()
        self.failed_tests = set()

    def pytest_runtest_setup(item):
        # called for running each test in 'a' directory
        # print("setting up", item)
        pass

    def pytest_runtest_logstart(nodeid, location):
        """
            :param str nodeid: full id of the item
            :param location: a triple of ``(filename, linenum, testname)``
        """
        # print(f"pytest_runtest_logstart {location}", nodeid)
        pass

    def pytest_runtest_logfinish(nodeid, location):
        """ signal the complete finish of running a single test item.

        This hook will be called **after** :func:`pytest_runtest_setup`, :func:`pytest_runtest_call` and
        :func:`pytest_runtest_teardown` hooks.

        :param str nodeid: full id of the item
        :param location: a triple of ``(filename, linenum, testname)``
        """
        # print(f"pytest_runtest_logfinish {location}", nodeid)

    def pytest_exception_interact(node, call, report):
        """called when an exception was raised which can potentially be
        interactively handled.

        This hook is only called if an exception was raised
        that is not an internal exception like ``skip.Exception``.
        """
        # pprint(call)
        # print(f"pytest_exception_interact {call}")

        # pprint(vars(report))
        pass

    def pytest_runtest_logreport(self, report):
        # pprint(vars(report))
        if report.when == 'setup':
            if report.outcome == 'skipped':
                self.passed_tests.add(report.nodeid)

        if report.when == 'teardown':
            pass

        if report.when == 'call':
            if report.outcome == 'skipped':
                self.passed_tests.add(report.nodeid)
                return
            if report.passed:
                self.passed_tests.add(report.nodeid)
            if not report.passed:
                self.failed_tests.add(report.nodeid)

    def guess_run_status(self, test_name):
        if len(self.failed_tests) > 0:
            return False

        if len(self.passed_tests) <= 0:
            return False
        else:
            return True
