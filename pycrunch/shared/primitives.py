class TestMetadata:
    def __init__(self, filename, name, module, fqn, state):
        self.state = state
        self.fqn = fqn
        self.module = module
        self.name = name
        self.filename = filename
