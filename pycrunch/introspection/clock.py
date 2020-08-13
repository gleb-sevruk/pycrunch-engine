import time


class Clock:
    def now(self):
        # floating point value in seconds
        return time.perf_counter()


clock = Clock()