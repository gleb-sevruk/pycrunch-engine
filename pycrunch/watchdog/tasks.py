class AbstractWatchdogTask:
    name: str
    def run(self):
        raise Exception('Abstract method call in AbstractWatchdogTask->run.')


class TestExecutionBeginTask(AbstractWatchdogTask):
    def __init__(self, total_tests: int):
        self.total_tests = total_tests
        self.name = 'watchdog_begin'


class TestExecutionEndTask(AbstractWatchdogTask):
    def __init__(self):
        self.name = 'watchdog_end'


class TerminateTestExecutionTask(AbstractWatchdogTask):
    def __init__(self):
        self.name = 'watchdog_terminate'
