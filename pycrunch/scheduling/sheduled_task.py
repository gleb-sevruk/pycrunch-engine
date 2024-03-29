from uuid import uuid4


class TestRunPlan:
    __test__ = False

    def __init__(self, tests, id=None):
        self.id = str(uuid4()) if not id else id
        self.tests = tests
