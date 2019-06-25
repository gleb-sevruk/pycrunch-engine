import sys

from pycrunch.plugins.pytest_support.hot_reload import unload_candidates


class ModuleCleanup():
    def __init__(self):
        self.modules_before = []

    def __enter__(self):
        self.modules_before = set(sys.modules)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        modules_after = set(sys.modules)
        difference = set(modules_after).difference(self.modules_before)
        modules_for_unload = unload_candidates(difference)
        for m in modules_for_unload:
            del sys.modules[m]
