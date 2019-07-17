import time


class Clock:
    def now(self):
        return time.perf_counter()


clock = Clock()