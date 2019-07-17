from collections import deque


def serialize_intervals(root_interval):
    result = []
    intervals_dict = []
    events = []
    for interval in root_interval.intervals:
        intervals_dict.append(serialize_intervals(interval))
    for evt in root_interval.events:
        events.append(dict(name=evt.name, timestamp=evt.relative_timestamp()))
    result.append(dict(name=root_interval.name, events=events, intervals=intervals_dict, start=root_interval.started_at, end=root_interval.stopped_at, duration=root_interval.duration()))
    return result


class ExecutionHistory:
    def __init__(self):
        self.timelines = deque(maxlen=100)

    def save(self, timeline):
        self.timelines.append(timeline)

    def to_json(self):
        results = []
        my_copy = self.timelines.copy()
        for x in my_copy:
            results.append(dict(timeline_name=x.name, duration=x.duration(), intervals=serialize_intervals(x.root)))
        return dict(results=results)


execution_history = ExecutionHistory()