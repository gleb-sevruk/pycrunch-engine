from pycrunch.insights.variables_inspection import EmptyInsightTimeline


class ErrorRecord: 
    def __init__(self, etype, value, current_traceback):
        self.current_traceback = current_traceback
        self.value = value
        self.etype = etype


failed_status = 'failed'
success_status = 'success'
queued_status = 'queued'

class ExecutionResult:
    def __init__(self):
        self.captured_output = None
        self.status = 'pending'
        self.intercepted_exception = None
        self.state_timeline = EmptyInsightTimeline()

    def record_exception(self, etype, value, current_traceback):
        self.intercepted_exception = ErrorRecord(etype=etype, value=value, current_traceback=current_traceback)

    def run_did_fail(self):
        self.status = failed_status

    def run_did_queued(self):
        self.status = queued_status

    def run_did_succeed(self):
        self.status = success_status

    def output_did_become_available(self, captured_output):
        self.captured_output = captured_output

    def state_timeline_did_become_available(self, state_timeline):
        self.state_timeline = state_timeline
    
    @classmethod
    def create_failed_with_reason(cls, reason):
        """

        :type reason: str
        """
        x = cls()
        x.run_did_fail()
        x.output_did_become_available(reason)
        return x
