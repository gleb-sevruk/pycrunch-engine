
class AbstractMessage():
    kind = 'abstract'

class HandshakeMessage(AbstractMessage):
    def __init__(self, task_id):
        self.task_id = task_id
        self.kind = 'handshake'
        # self.bytes_junk = bytearray(998765)

class ScheduledTaskDefinitionMessage(AbstractMessage):
    def __init__(self, task):
        self.task = task
        self.kind = 'test-run-task'

class TestResultsAvailableMessage(AbstractMessage):
    def __init__(self, results):
        self.results = results
        self.kind = 'test_run_results'


class TestRunTimingsMessage(AbstractMessage):
    def __init__(self, timeline):
        self.timeline = timeline
        self.kind = 'timings'


class CloseConnectionMessage(AbstractMessage):
    def __init__(self, task_id):
        self.task_id = task_id
        self.kind = 'close'

