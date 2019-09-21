from uuid import uuid4


class TestRunPlan():
    def __init__(self, tests):
        self.id = str(uuid4())
        self.tests = tests
