class Configuration:
    def __init__(self):
        self.runtime_engine = 'pytest'
        self.available_engines = ['simple', 'pytest']

    def runtime_engine_will_change(self, new_engine):
        self.throw_if_not_supported_engine(new_engine)
        self.runtime_engine = new_engine

    def throw_if_not_supported_engine(self, new_engine):
        if new_engine not in self.available_engines:
            raise Exception(f'engine {new_engine} not available. Possible options: {self.available_engines}')


config = Configuration()