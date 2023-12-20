import traceback

from pycrunch.plugins.pytest_support.exception_utilities import (
    get_originating_frame_and_location,
    stringify_locals,
)
from pycrunch.session.recorded_exception import RecordedException


class PyTestInterceptionPlugin:
    def __init__(self, tests_to_run):
        self.passed_tests = set()
        self.failed_tests = set()
        self.recorded_exception = None  # type: RecordedException

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
        """signal the complete finish of running a single test item.

        This hook will be called **after** :func:`pytest_runtest_setup`, :func:`pytest_runtest_call` and
        :func:`pytest_runtest_teardown` hooks.

        :param str nodeid: full id of the item
        :param location: a triple of ``(filename, linenum, testname)``
        """
        # print(f"pytest_runtest_logfinish {location}", nodeid)

    def pytest_exception_interact(self, node, call, report):
        exc_type = (
            call.excinfo.type
        )  # The exception type, e.g. AssertionError, ValueError, etc.
        exc_value = (
            call.excinfo.value
        )  # The exception instance, containing the error message and other details
        exc_traceback = call.excinfo.tb  # The traceback object

        # Get the formatted traceback as a list of strings
        # formatted_traceback = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # Print the exception details for demonstration purposes

        formatted_traceback = traceback.format_exception(
            exc_type, exc_value, exc_traceback
        )
        full_traceback_str = "".join(formatted_traceback)

        frame, filename, line_number, frames = get_originating_frame_and_location(  # noqa F841
            exc_traceback
        )
        _locals = stringify_locals(frame)
        # print(f"locals: {locals}")
        # print(f"Most recent stack frame: {frame}")
        # print(f"Filename: {filename}")
        # print(f"Line number: {line_number}")
        DISABLE_LOCALS = False
        if DISABLE_LOCALS:
            _locals = {}
        self.recorded_exception = RecordedException(
            filename, line_number, full_traceback_str, _locals
        )

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

    def get_recorded_exception(self, test_name):
        return self.recorded_exception
