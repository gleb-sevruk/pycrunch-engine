# Interval -> contains start, end, nested intervals, and markers (relative to interval)
import os
from datetime import datetime

from pycrunch.introspection.clock import clock
from collections import deque


class Interval:
    def __init__(self):
        self.intervals = []
        self.events = []
        self.name = None
        self.started_at = None
        self.stopped_at = None

    def duration(self):
        return round(self.stopped_at - self.started_at, 3)

    def start(self):
        self.started_at = clock.now()

    def stop(self):
        self.stopped_at = clock.now()

    def begin_nested_interval(self, name):
        interval = Interval()
        interval.start()
        interval.name = name
        self.intervals.append(interval)
        return interval

    def mark_event(self, name, relative_to):
        self.events.append(Marker(name, relative_to))

    def to_console(self, indent=0):
        join = " ".join([" " for x in range(1, indent + 1)])
        print(f'{join}  {self.name} [{self.started_at} ... {self.stopped_at}] ({self.duration():.3f} seconds)')
        for evt in self.events:
            print(f'    {join}  [event] [{evt.relative_timestamp()}] {evt.name} at {evt.timestamp} (in {self.name}) ')

        for interval in self.intervals:
            interval.to_console(indent=indent+3)



class Marker:
    def __init__(self, name, relative_to):
        self.relative_to = relative_to
        self.timestamp = clock.now()
        self.name = name

    def relative_timestamp(self):
        # relative to entire Timeline
        return round(self.timestamp - self.relative_to, 3)

class Timeline:
    # todo use interval stacks
    def __init__(self, name):
        self.name = name
        self.root = Interval()
        self.root.name = name
        self.intervals_stack = deque()
        self.intervals_stack.append(self.root)
        self.relative_to = None

    def start(self):
        self.relative_to = clock.now()
        self.root.start()

    def stop(self):
        self.root.stop()

    def duration(self):
        # in seconds
        return self.root.duration()

    def begin_nested_interval(self, name):
        self.intervals_stack.append(self.current_interval().begin_nested_interval(name))

    def current_interval(self):
        return self.intervals_stack[-1]

    def end_nested_interval(self):
        current_interval = self.intervals_stack.pop()
        current_interval.stop()

    def to_console(self):
        self.root.to_console()

    def mark_event(self, event_name):
        # print(f'[{os.getpid()}] {datetime.now().isoformat()} {event_name}')
        self.current_interval().mark_event(event_name, self.relative_to)
        pass

