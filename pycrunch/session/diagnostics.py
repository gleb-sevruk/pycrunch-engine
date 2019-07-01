import os
import sys


class DiagnosticEngine:

    def summary(self):
        return dict(env=self.get_env(), modules=self.get_modules())

    def get_env(self):
        return dict(os.environ.items())

    def get_modules(self):
        return list(sys.modules)

diagnostic_engine = DiagnosticEngine()