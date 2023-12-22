# Event handler for the 'my_response' event
import os
from pathlib import Path
from time import sleep
from typing import List, Optional
from unittest import TestCase

import socketio

from pycrunch.insights import trace
from pycrunch_integration_tests.models import (
    CombinedCoverage,
    DiscoveredTestModel,
    TestRunCompletedModel,
)

PYCRUNCH_API_URL = os.getenv("PYCRUNCH_API_URL", "http://websocket_app:11016")


def print_info():
    print("---------------------------")
    print("Running integration tests...")
    print(f"Using API_URL={PYCRUNCH_API_URL}")
    print("---------------------------\n")


print_info()


class EngineState:
    version: Optional[dict]
    tests_discovered: Optional[List[DiscoveredTestModel]]
    test_run_results: Optional[dict[str, TestRunCompletedModel]]

    def __init__(self):
        self.tests_discovered = None
        self.test_run_results = {}
        self.combined_coverage = []
        self.status = 'initial'
        self.version = None

    def connection_established(self, data: dict):
        self.status = 'connected'
        self.version = data.get('version')

    def discovery_completed(self, data: dict):
        self.status = 'discovery_completed'
        self.tests_discovered = [DiscoveredTestModel(**item) for item in data['tests']]

    def combined_coverage_updated(self, data):
        self.combined_coverage.clear()
        for each in data['combined_coverage']:
            self.combined_coverage.append(CombinedCoverage(**each))
        pass

    def find_file_in_combined_coverage_by_suffix(
        self, filename_to_find: str
    ) -> Optional[CombinedCoverage]:
        for each in self.combined_coverage:
            if each.filename.endswith(filename_to_find):
                return each
        return None

    def test_run_completed(self, data):
        fqn_to_result = data['coverage']['all_runs']
        for k, v in fqn_to_result.items():
            self.test_run_results[k] = TestRunCompletedModel(**v)


def my_response_handler(data, state: EngineState):
    current_event_type = data['event_type']
    if current_event_type == 'connected':
        state.connection_established(data)
    elif current_event_type == 'discovery_did_become_available':
        state.discovery_completed(data)
    elif current_event_type == 'combined_coverage_updated':
        state.combined_coverage_updated(data)
    elif current_event_type == 'test_run_completed':
        state.test_run_completed(data)

    trace(**{data['event_type']: data})
    if 'tests' in data:
        trace(tests=data['tests'])


# Historically all events were sent via `my event` keyword. This is a legacy from the time from 0.5
EVENT_NAME = 'my event'

ROOT_PATH = '/Users/gleb/code/pycrunch/'


def find_by_fqn(
    tests_discovered: List[DiscoveredTestModel], fqn: str
) -> Optional[DiscoveredTestModel]:
    for test in tests_discovered:
        if test.fqn == fqn:
            return test
    return None


def assert_discovery_valid(tests_discovered: List[DiscoveredTestModel]):
    expected_tests = [
        DiscoveredTestModel(
            filename='/Users/gleb/code/pycrunch/integration_tests/test_folder/test_sample.py',
            fqn='test_sample:test_one',
            module='test_sample',
            name='test_one',
            pinned=False,
            state='pending',
        ),
        DiscoveredTestModel(
            filename='/Users/gleb/code/pycrunch/integration_tests/test_folder/test_sample.py',
            fqn='test_sample:test_two',
            module='test_sample',
            name='test_two',
            pinned=False,
            state='pending',
        ),
        DiscoveredTestModel(
            filename='/Users/gleb/code/pycrunch/integration_tests/test_folder/test_second.py',
            fqn='test_second:test_one',
            module='test_second',
            name='test_one',
            pinned=False,
            state='pending',
        ),
        DiscoveredTestModel(
            filename='/Users/gleb/code/pycrunch/integration_tests/test_folder/test_second.py',
            fqn='test_second:test_two',
            module='test_second',
            name='test_two',
            pinned=False,
            state='pending',
        ),
        DiscoveredTestModel(
            filename='/Users/gleb/code/pycrunch/integration_tests/test_folder/tests_in_subfolder/test_one.py',
            fqn='tests_in_subfolder.test_one:test_first',
            module='tests_in_subfolder.test_one',
            name='test_first',
            pinned=False,
            state='pending',
        ),
    ]
    # Can be more than is this array
    # assert len(tests_discovered) == len(expected_tests)
    for expected_test in expected_tests:
        actual_test = find_by_fqn(tests_discovered, expected_test.fqn)
        assert (
            actual_test is not None
        ), f'Waited for {expected_test.fqn} to be in discovery results'
        assert (
            Path(actual_test.filename).parts[-3:]
            == Path(expected_test.filename).parts[-3:]
        )
        assert actual_test.fqn == expected_test.fqn
        assert actual_test.module == expected_test.module
        assert actual_test.name == expected_test.name
        assert actual_test.pinned == expected_test.pinned
        assert actual_test.state == expected_test.state


class SocketIOContextManager:
    def __init__(self, url, event_handler):
        self.url = url
        self.event_handler = event_handler
        self.client = None

    def __enter__(self):
        self.client = socketio.Client()
        self.client.on('event', self.event_handler)
        self.client.connect(self.url, transports='websocket')
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't forget to disconnect when you're done
        self.client.disconnect()


class TestProblem(TestCase):
    state: EngineState

    def setUp(self):
        self.state = EngineState()

    def test_initial_state(self):
        assert self.state.status == 'initial'

    def test_initial_discovery_should_find_tests(self):
        # Create a Socket.IO client
        with self.connect_to_pycrunch() as sio:
            sleep(1)
            assert self.state.status == 'connected'

            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)

            trace(self.state.tests_discovered)

            assert_discovery_valid(self.state.tests_discovered)

    def test_run_test_should_change_status(self):
        # Create a Socket.IO client
        with self.connect_to_pycrunch() as sio:
            sleep(1)

            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)

    def test_when_ran_status_changes_to_success(self):
        with self.connect_to_pycrunch() as sio:
            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)
            assert len(self.state.tests_discovered) > 0
            assert self.state.status == 'discovery_completed'

            sio.emit(
                EVENT_NAME,
                Actions.run_tests(['test_sample:test_one', 'test_sample:test_two']),
            )
            sleep(1)
            test_one = find_by_fqn(self.state.tests_discovered, 'test_sample:test_one')
            test_two = find_by_fqn(self.state.tests_discovered, 'test_sample:test_two')
            assert test_one.state == 'success'
            assert test_two.state == 'success'

    def test_when_ran_status_capture_output(self):
        with self.connect_to_pycrunch() as sio:
            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)
            assert len(self.state.tests_discovered) > 0
            assert self.state.status == 'discovery_completed'

            sio.emit(EVENT_NAME, Actions.run_tests(['test_sample:test_one']))
            sleep(2)
            test_one = find_by_fqn(self.state.tests_discovered, 'test_sample:test_one')
            assert test_one.state == 'success'
            assert (
                'output from test_one'
                in self.state.test_run_results['test_sample:test_one'].captured_output
            )

    def test_when_ran_should_have_single_file_coverage(self):
        with self.connect_to_pycrunch() as sio:
            sleep(1)

            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)
            assert len(self.state.tests_discovered) > 0
            assert self.state.status == 'discovery_completed'

            sio.emit(EVENT_NAME, Actions.run_tests(['test_sample:test_one']))
            sleep(2)
            test_one = find_by_fqn(self.state.tests_discovered, 'test_sample:test_one')
            assert test_one.state == 'success'
            assert len(self.state.test_run_results['test_sample:test_one'].files) > 0
            file_coverage_shared = self.state.test_run_results[
                'test_sample:test_one'
            ].find_file_by_suffix("test_folder/shared_file.py")
            file_coverage_test_file = self.state.test_run_results[
                'test_sample:test_one'
            ].find_file_by_suffix("test_folder/test_sample.py")
            assert file_coverage_shared is not None
            assert file_coverage_test_file is not None

            assert (
                2 in file_coverage_shared.lines_covered
            ), 'Method body was not covered'
            assert 5 in file_coverage_test_file.lines_covered
            assert 6 in file_coverage_test_file.lines_covered
            assert 10 not in file_coverage_test_file.lines_covered

    def test_when_test_one_ran_should_have_combined_coverage(self):
        with self.connect_to_pycrunch() as sio:
            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)
            assert len(self.state.tests_discovered) > 0
            assert self.state.status == 'discovery_completed'

            sio.emit(EVENT_NAME, Actions.run_tests(['test_sample:test_one']))
            sleep(2)
            test_one = find_by_fqn(self.state.tests_discovered, 'test_sample:test_one')
            assert test_one.state == 'success'
            cov = self.state.find_file_in_combined_coverage_by_suffix(
                'test_folder/test_sample.py'
            )
            assert (
                cov is not None
            ), 'Combined coverage for `test_folder/test_sample.py` should be available'
            assert ['test_sample:test_one'] == cov.lines_with_entrypoints['5']
            assert ['test_sample:test_one'] == cov.lines_with_entrypoints['6']

    def test_when_two_tests_ran_should_have_combined_coverage(self):
        with self.connect_to_pycrunch() as sio:
            sio.emit(EVENT_NAME, Actions.discovery())
            sleep(1)
            assert len(self.state.tests_discovered) > 0
            assert self.state.status == 'discovery_completed'

            sio.emit(
                EVENT_NAME,
                Actions.run_tests(['test_sample:test_one', 'test_sample:test_two']),
            )
            sleep(2)
            test_one = find_by_fqn(self.state.tests_discovered, 'test_sample:test_one')
            assert test_one.state == 'success'
            cov = self.state.find_file_in_combined_coverage_by_suffix(
                'test_folder/test_sample.py'
            )
            assert (
                cov is not None
            ), 'Combined coverage for `test_folder/test_sample.py` should be available'
            assert ['test_sample:test_one'] == cov.lines_with_entrypoints['5']
            assert ['test_sample:test_one'] == cov.lines_with_entrypoints['6']

            assert ['test_sample:test_two'] == cov.lines_with_entrypoints['10']

    def connect_to_pycrunch(self):
        self.state = EngineState()
        return SocketIOContextManager(
            PYCRUNCH_API_URL, lambda data: my_response_handler(data, self.state)
        )


class Actions:
    @staticmethod
    def discovery():
        return {'action': 'discovery'}

    @staticmethod
    def halt():
        return {'action': 'halt'}

    @staticmethod
    def run_tests(fqns: List[str]):
        return {'action': 'run-tests', 'tests': [{'fqn': fqn} for fqn in fqns]}
