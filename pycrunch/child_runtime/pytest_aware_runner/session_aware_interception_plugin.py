import string
import traceback
from pprint import pp
from typing import Dict, Optional

from coverage import CoverageData

from pycrunch.api.serializers import CoverageRun
from pycrunch.child_runtime.coverage_hal import CoverageAbstraction
from pycrunch.child_runtime.pytest_aware_runner.pytest_state_machine import PytestStateMachine
from pycrunch.introspection.timings import Timeline
from pycrunch.plugins.pytest_support.exception_utilities import get_originating_frame_and_location, stringify_locals
from pycrunch.runner.single_test_execution_result import SingleTestExecutionResult
from pycrunch.session.recorded_exception import RecordedException

state_transitions = ['initial', 'fixtures', 'test']


DISABLE_COVERAGE = False



class PyTestSessionAwarePycrunchPlugin:
    def __init__(self,  timeline, child_config, coverage_exclusions):
        self.child_config = child_config
        self.timeline = timeline  # type: Timeline
        self.passed_tests = set()
        self.failed_tests = set()
        self.tests_to_run = []  # type: list[Dict]
        self.recorded_exception = None  # type: RecordedException
        # self.cov = coverage.Coverage(timid=True, data_file=None)
        should_disable_coverage = DISABLE_COVERAGE
        if self.child_config.enable_remote_debug:
            should_disable_coverage = True
        self.cov = CoverageAbstraction(should_disable_coverage, coverage_exclusions, self.timeline)
        # steal session from pytest
        self.raw_session = None  # type: pytest.Session
        self.state_machine = PytestStateMachine(timeline)

        self.intermediate_results = dict()  # type: Dict[str, CoverageRun]



    def tests_will_run(self, tests_to_run):
        self.tests_to_run = tests_to_run

    def pytest_configure(self, config):
        """
        # Called after command-line options have been parsed, allowing you to modify the pytest configuration.
        @param config:
        @return:
        """
        self.timeline.mark_event(f"pytest_configure {config}")

    def pytest_sessionstart(self, session):
        """
        Called at the start of a pytest session.
        @param session:
        @return:
        """
        if self.state_machine.current_state() == 'initial':
            self.state_machine.next_state('fixtures')
            self.cov.start()
            self.cov.switch_context('fixtures')

        self.timeline.mark_event(f"pytest_sessionstart {session}")

    def pytest_fixture_setup(self, fixturedef, request):
        """
        Called before a fixtures is setup.
        """
        self.timeline.mark_event(f"pytest_fixture_setup {fixturedef} {request}")

    def pytest_fixture_post_finalizer(self, fixturedef, request):
        """
            Called after a fixture has been torn down.
        """
        # self.timeline.mark_event(f"pytest_fixture_post_finalizer {fixturedef} {request}")
        pass

    def pytest_runtest_setup(self, item):
        # called for running each test in 'a' directory
        self.timeline.mark_event(f"setting up {item}")
        pass

    def pytest_collect_file(self, path, parent):
        self.timeline.mark_event(f"pytest_collect_file {path} {parent}")
        pass

    def pytest_runtestloop(self, session):
        """
        Perform the main runtest loop (after collection finished).

        @return:
        """
        self.timeline.mark_event(f"pytest_runtestloop {session}")
        self.raw_session = session
        pass
    def _print_cov(self):
        x = self.cov.raw().get_data()  # type: CoverageData
        x.set_query_contexts('fixtures')
        x.measured_files()
        for _file in x.measured_files():
            z = x.contexts_by_lineno(_file)
            pp(_file)
            pp(z)

    def pytest_runtest_call(self, item):
        self.timeline.mark_event(f"pytest_runtest_call, item={item}")
        fqn = self.node_id_without_parametrized(item.nodeid)
        if self.state_machine.current_state() == 'fixtures':
            # self.cov.stop()
            self.timeline.mark_event(f"pytest_runtest_call switch_context to {fqn}")
            self.cov.switch_context(fqn)

        self.timeline.mark_event("pytest_runtest_call, searching for metadata")
        tm = self.find_metadata_by_nodeid(item)
        if tm is None:
            self.timeline.mark_event(f"[CRITICAL] !!! pytest_runtest_call could not find metadata for {item}")
            raise Exception(f"Could not find metadata for {item}")
        self.timeline.mark_event("pytest_runtest_call, metadata found")
        self.state_machine.will_run_test(tm)
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=50147, stdoutToServer=True, stderrToServer=True)
        self.timeline.mark_event(f"pytest_runtest_call {item} -- complete")

    def node_id_without_parametrized(self, pytest_nodeid):
        target_node_id = pytest_nodeid
        param_index = pytest_nodeid.find('[')
        if param_index != -1:
            # remove the suffix starting from "[" character
            target_node_id = pytest_nodeid[:param_index]

        return target_node_id

    def pytest_runtest_logstart(self, nodeid, location):
        """
            :param str nodeid: full id of the item
            :param location: a triple of ``(filename, linenum, testname)``
        """
        self.state_machine.inject_variable_timeline()
        self.timeline.mark_event(f"pytest_runtest_logstart nodeid={nodeid} {location=}")

    def pytest_runtest_logfinish(self, nodeid, location):
        """ signal the complete finish of running a single test item.

        This hook will be called **after** :func:`pytest_runtest_setup`, :func:`pytest_runtest_call` and
        :func:`pytest_runtest_teardown` hooks.

        :param str nodeid: full id of the item
        :param location: a triple of ``(filename, linenum, testname)``
        """

        self.timeline.mark_event(f"pytest_runtest_logfinish {nodeid} - {location}", )
        execution_result = SingleTestExecutionResult()  # type: SingleTestExecutionResult
        execution_result.output_did_become_available("TODO Capture it!!")
        variable_timeline = self.state_machine.pop_variable_timeline()
        execution_result.state_timeline_did_become_available(variable_timeline)
        effective_node_id = self.node_id_without_parametrized(nodeid)
        if effective_node_id in self.failed_tests:
            execution_result.run_did_fail()
        elif effective_node_id in self.passed_tests:
            execution_result.run_did_succeed()

        test_envelop = self.state_machine.did_run_test(nodeid)
        test_meta = test_envelop.test_metadata

        run_results = CoverageRun(test_meta['fqn'], test_envelop.duration(), test_meta, execution_result)
        data = self.cov.raw().get_data()
        params = ['fixtures', self.node_id_without_parametrized(nodeid)]
        self.timeline.mark_event(f"set_query_contexts {params}", )
        data.set_query_contexts(params)
        run_results.store_files_coverage(self.cov.parse_all_hit_lines())

        data.set_query_contexts(None)
        self.timeline.mark_event(f"set_query_contexts to -> None", )

        self.intermediate_results[test_meta['fqn']] = run_results

    def find_metadata_by_nodeid(self, pytest_item) -> Optional[Dict]:
        target_node_id = self.node_id_without_parametrized(pytest_item.nodeid)  # type: str
        # Hack, parametrized are not supported in full on discovery stage, so we run them as single test

        for test_meta in self.tests_to_run:
            fqn = f"{test_meta['filename']}::{test_meta['name']}"
            if fqn.endswith(target_node_id):
                return test_meta


    def get_results(self):
        return self.intermediate_results

    def pytest_exception_interact(self, node, call, report):
        self.timeline.mark_event(f'pytest_exception_interact {node} {call} {report}')
        exc_type = call.excinfo.type  # The exception type, e.g. AssertionError, ValueError, etc.
        exc_value = call.excinfo.value  # The exception instance, containing the error message and other details
        exc_traceback = call.excinfo.tb  # The traceback object

        # Get the formatted traceback as a list of strings
        # formatted_traceback = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # Print the exception details for demonstration purposes

        formatted_traceback = traceback.format_exception(exc_type, exc_value, exc_traceback)
        full_traceback_str = "".join(formatted_traceback)

        frame, filename, line_number, frames = get_originating_frame_and_location(exc_traceback)
        _locals = stringify_locals(frame)
        # print(f"locals: {locals}")
        # print(f"Most recent stack frame: {frame}")
        # print(f"Filename: {filename}")
        # print(f"Line number: {line_number}")
        DISABLE_LOCALS = False
        if DISABLE_LOCALS:
            _locals = {}
        self.recorded_exception = RecordedException(filename, line_number, full_traceback_str, _locals)

    def pytest_runtest_logreport(self, report):
        """
        Called multiple times during the runtest protocol.
        @param report:
        @return:
        """
        self.timeline.mark_event(f"pytest_runtest logreport {report=}")
        # pprint(vars(report))
        if report.when == 'setup':
            if report.outcome == 'skipped':
                self.passed_tests.add(self.node_id_without_parametrized(report.nodeid))

        if report.when == 'teardown':
            pass

        if report.when == 'call':
            if report.outcome == 'skipped':
                self.passed_tests.add(self.node_id_without_parametrized(report.nodeid))
                return
            if report.passed:
                self.passed_tests.add(self.node_id_without_parametrized(report.nodeid))
            if not report.passed:
                self.failed_tests.add(self.node_id_without_parametrized(report.nodeid))

    def pytest_sessionfinish(self, session, exitstatus):
        self.timeline.mark_event(f"pytest_sessionfinish {session} {exitstatus}")
        # Generate and display the coverage report
        self.cov.stop()
        # self._print_cov()
        # self.cov.raw().report(contexts=".*")
        # self.cov.raw().html_report(show_contexts=True)

    def get_recorded_exception(self, test_name):
        return self.recorded_exception


"""
pytest_addoption(parser)
Called to add command-line options to the pytest parser.

pytest_cmdline_parse(config, args)
Called when pytest parses the command-line arguments.

pytest_configure(config)
Called after command-line options have been parsed, allowing you to modify the pytest configuration.

pytest_sessionstart(session)
Called at the start of a pytest session.

pytest_collection(session)
Called to perform test collection.

pytest_collect_file(path, parent)
Called to determine if a file should be collected.

pytest_collect_directory(path, parent)
Called to filter directories from the collection.

pytest_collection_modifyitems(config, items)
Called after collection is complete, allowing you to modify the collected items.

pytest_sessionfinish(session, exitstatus)
Called at the end of a pytest session.

pytest_runtest_protocol(item, nextitem)
Called to implement the runtest protocol for a specific test item.

pytest_runtest_setup(item)
Called before the test is executed.

pytest_runtest_call(item)
Called to execute the test item.

pytest_runtest_teardown(item, nextitem)
Called after the test is executed.

pytest_runtest_makereport(item, call)
Called to create a test report for a test item.

pytest_runtest_logstart(nodeid, location)
Called before a test starts running, allowing you to log the start of the test.

pytest_runtest_logfinish(nodeid, location)
Called after a test finishes running, allowing you to log the end of the test.

pytest_report_header(config)
Called to generate the header of the test report.

pytest_report_teststatus(report, config)
Called to determine the status of a test report.

pytest_terminal_summary(terminalreporter, exitstatus, config)
Called at the end of the test session, allowing you to add a summary to the terminal report.

pytest_fixture_setup(fixturedef, request)
Called before a fixtures is setup.

def pytest_fixture_post_finalizer(fixturedef, request):
    Called after a fixture has been torn down.
    

"""