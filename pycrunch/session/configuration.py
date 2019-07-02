import io
from pathlib import Path

import logging

import yaml

logger = logging.getLogger(__name__)

class Configuration:
    def __init__(self):
        self.discovery_exclusions = ()
        self.working_directory = Path('.')
        self.runtime_engine = 'django'
        self.django_ready = False
        # self.runtime_engine = 'pytest'
        self.available_engines = ['simple', 'pytest', 'django']

    def runtime_engine_will_change(self, new_engine):
        self.throw_if_not_supported_engine(new_engine)
        self.runtime_engine = new_engine

    def prepare_django(self):
        # if not self.django_ready:
        if self.runtime_engine == 'django' and not self.django_ready:
            logger.info('!!! Importing Django and calling django.setup')
            try:
                import django
                django.setup()
            except Exception as e:
                logger.exception('Failed to import or set up django! Are you sure it is django project?', exc_info=e)
            self.django_ready = True


    def throw_if_not_supported_engine(self, new_engine):
        if new_engine not in self.available_engines:
            raise Exception(f'engine {new_engine} not available. Possible options: {self.available_engines}')

    def load_runtime_configuration(self):
        joinpath = self.working_directory.joinpath('.pycrunch-config.yaml')
        print(str(joinpath.absolute()))
        print(joinpath)
        try:
            with io.open(joinpath, encoding='utf-8') as f:
                x = yaml.safe_load(f)
                discovery = x.get('discovery', None)
                if discovery:
                    exc = discovery.get('exclusions', None)
                    if not hasattr(exc, "__len__"):
                        raise Exception('.pycrunch-config.yaml: discovery->exclusions should be array')
                    self.discovery_exclusions = tuple(exc)
                engine_config = x.get('engine', None)
                if engine_config:
                    runtime_engine_name = engine_config.get('runtime', None)
                    if runtime_engine_name:
                        self.runtime_engine_will_change(runtime_engine_name)
                print(x)
                print(f)
        except:
            print("configuration file not found")


config = Configuration()