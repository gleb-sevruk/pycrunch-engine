class ChildRuntimeConfig:
    def __init__(self):
        self.load_pytest_plugins = False
        self.enable_remote_debug = False
        self.remote_debug_port = -1
        self.runtime_engine = 'pytest'
        self.collect_timings = False

    def use_engine(self, new_engine):
        self.runtime_engine = new_engine

    def enable_remote_debugging(self, port_to_use):
        self.enable_remote_debug = True
        self.remote_debug_port = int(port_to_use)

    def enable_timing_collection(self):
        self.collect_timings = True


child_config = ChildRuntimeConfig()
