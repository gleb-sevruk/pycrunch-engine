from collections import deque
from typing import Dict

from pycrunch.insights.variables_inspection import InsightTimeline, inject_timeline
from pycrunch.introspection.clock import clock

class TestEnvelope:
    def __init__(self, test_metadata: Dict, start_time: float):
        self.test_metadata = test_metadata
        self.start_time = start_time
        self.end_time = None  # type: Optional[float]

    def duration(self) -> float:
        return self.end_time - self.start_time


class PytestStateMachine:
    def __init__(self, timeline):
        self.timeline = timeline
        self.completed_tests = set()
        self.running_tests = deque()
        self.current_test = None
        self.state = 'initial'
        self.current_vars_timeline = deque()
        self.start_time = clock.now()

    def will_run_test(self, test_metadata: Dict):
        self.timeline.mark_event(f"PytestStateMachine->will_run_test {test_metadata['fqn']}")
        self.current_test = test_metadata['fqn']
        self.running_tests.append(TestEnvelope(test_metadata, clock.now()))

    def next_state(self, name: str):
        self.timeline.mark_event(f"PytestStateMachine->next_state {self.state} -> {name}")
        self.state = name

    def current_state(self) -> str:
        return self.state

    def inject_variable_timeline(self):
        state_timeline = InsightTimeline(clock=clock)
        state_timeline.start()
        self.current_vars_timeline.append(state_timeline)
        inject_timeline(state_timeline)

    def pop_variable_timeline(self) -> InsightTimeline:
        return self.current_vars_timeline.pop()

    def did_run_test(self, test: str) -> TestEnvelope:
        self.timeline.mark_event(f"PytestStateMachine->did_run_test {test}")
        popped = self.running_tests.pop()  # type: TestEnvelope
        popped.end_time = clock.now()
        assert len(self.running_tests) == 0
        assert popped.test_metadata['fqn'] == self.current_test
        self.current_test = None
        return popped
