import io
from pathlib import Path

import logging

import yaml

logger = logging.getLogger(__name__)

class Configuration:
    def __init__(self):
        self.allowed_modes = ['auto', 'manual', 'pinned']
        self.discovery_exclusions = ()
        self.working_directory = Path('.')
        self.runtime_engine = 'django'
        self.django_ready = False
        self.engine_directory = 'unknown'
        self.engine_mode = 'auto'
        self.pinned_tests = set()
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

    def set_engine_directory(self, engine_directory):
        self.engine_directory = engine_directory

    def load_runtime_configuration(self):
        print(str(self.configuration_file_path().absolute()))
        print(self.configuration_file_path())
        try:
            with io.open(self.configuration_file_path(), encoding='utf-8') as f:
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
                    runtime_mode = engine_config.get('mode', None)
                    if runtime_mode:
                        self.runtime_mode_will_change(runtime_mode)

                pinned_tests = x.get('pinned-tests', None)
                if pinned_tests:
                    self.apply_pinned_tests(pinned_tests)
                print(x)
                print(f)
        except Exception as e:
            print("Exception during processing configuration\n" + str(e))

    def configuration_file_path(self):
        return self.working_directory.joinpath('.pycrunch-config.yaml')

    def runtime_mode_will_change(self, runtime_mode):
        self.throw_if_mode_not_supported(runtime_mode)
        print(f'Engine execution mode will change from {self.engine_mode} to {runtime_mode}')
        self.engine_mode = runtime_mode

    def throw_if_mode_not_supported(self, runtime_mode):
        if runtime_mode not in self.allowed_modes:
            raise Exception(f"runtime mode {runtime_mode} not supported. Available options are: {self.allowed_modes}")

    def save_pinned_tests_config(self, fqns):
        self.apply_pinned_tests(fqns)
        existing_config = None
        with io.open(self.configuration_file_path(), encoding='utf-8', mode='r') as f:
            existing_config = yaml.safe_load(f)


        existing_config['pinned-tests'] = list(fqns)
        with io.open(self.configuration_file_path(), encoding='utf-8', mode='w') as f:
            yaml.dump(existing_config, f, default_flow_style=False)
        pass

    def is_test_pinned(self, fqn):
        return fqn in self.pinned_tests

    def apply_pinned_tests(self, pinned_tests):
        self.pinned_tests = set()
        for fqn in pinned_tests:
            self.pinned_tests.add(fqn)


config = Configuration()