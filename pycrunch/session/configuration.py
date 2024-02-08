import io
import logging
import multiprocessing
from os import environ
from pathlib import Path
from typing import List, Optional

import yaml

from pycrunch.constants import CONFIG_FILE_NAME
from pycrunch.session.auto_configuration import AutoConfiguration

logger = logging.getLogger(__name__)


class NoPathMapping:
    def map_to_local_fs(self, filename):
        return filename

    def map_local_to_remote(self, filename):
        return filename


class PathMapping:
    def __init__(self, path_in_container, path_on_local_ide):
        self.path_on_local_ide = path_on_local_ide
        self.path_in_container = path_in_container

    def map_to_local_fs(self, filename: str):
        return filename.replace(self.path_in_container, self.path_on_local_ide, 1)

    def map_local_to_remote(self, filename):
        return filename.replace(self.path_on_local_ide, self.path_in_container, 1)


class PycrunchException(Exception):
    pass


class Configuration:
    def __init__(self):
        self.allowed_modes = ['auto', 'manual', 'pinned']
        self.discovery_exclusions = ()
        self.coverage_exclusions = []
        self.working_directory = Path('.')
        self.django_ready = False
        self.engine_directory = 'unknown'
        self.engine_mode = 'auto'
        self.deep_inheritance = False
        self.pinned_tests = set()
        self.cpu_cores = self.get_default_cpu_cores()
        self.multiprocessing_threshold = 5
        self.execution_timeout_in_seconds = 60
        self.runtime_engine = 'pytest'
        self.available_engines = ['simple', 'pytest', 'django']
        self.environment_vars = dict()
        self.load_pytest_plugins = False
        self.path_mapping = NoPathMapping()
        self.enable_asyncio_debug = False
        self.enable_web_ui = False
        self.change_detection_root: str = self._get_working_directory()
        self.intellij_connector_version = 'unknown'
        self.module_prefixes = []
        self.function_prefixes = []

    def _get_working_directory(self):
        return str(Path('.').absolute())

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
                logger.exception(
                    'Failed to import or set up django! Are you sure it is django project?',
                    exc_info=e,
                )
            self.django_ready = True

    def throw_if_not_supported_engine(self, new_engine):
        if new_engine not in self.available_engines:
            raise Exception(
                f'engine {new_engine} not available. Possible options: {self.available_engines}'
            )

    def set_engine_directory(self, engine_directory):
        self.engine_directory = engine_directory

    def load_runtime_configuration(self):
        # This will output exact location of config file
        print(str(self.configuration_file_path().absolute()))
        print(self.configuration_file_path())

        auto_config = AutoConfiguration(self.configuration_file_path())
        auto_config.ensure_configuration_exist()

        try:
            with io.open(self.configuration_file_path(), encoding='utf-8') as f:
                self._load_config_now(f)
        except Exception as e:
            self.raise_configuration_error(e)

    def watch_for_config_changes(self):
        from pycrunch.api.shared import file_watcher

        logger.debug('watch_for_config_changes')
        file_watcher.watch([str(self.configuration_file_path().absolute())])

    def raise_configuration_error(self, e):
        print("Exception during processing configuration\n" + str(e))
        raise PycrunchException('configuration parse failed', e)

    def _load_config_now(self, f):
        x = yaml.safe_load(f)
        discovery = x.get('discovery', None)
        if discovery:
            exc = discovery.get('exclusions', None)
            if not hasattr(exc, "__len__"):
                raise Exception(
                    '.pycrunch-config.yaml: discovery->exclusions should be array'
                )
            self.discovery_exclusions = tuple(exc)
        engine_config = x.get('engine', None)
        if engine_config:
            self._load_runtime_configuration_engine(engine_config)
        pinned_tests = x.get('pinned-tests', None)
        if pinned_tests:
            self.apply_pinned_tests(pinned_tests)
        additional_env = x.get('env', None)
        if additional_env:
            self.apply_additional_env(additional_env)
        path_mapping = x.get('path-mapping', None)
        if path_mapping:
            self.apply_path_mapping(path_mapping)

        self.apply_coverage_exclusions(x.get('coverage-exclusions', None))

    def _load_runtime_configuration_engine(self, engine_config):
        runtime_engine_name = engine_config.get('runtime', None)
        if runtime_engine_name:
            self.runtime_engine_will_change(runtime_engine_name)
        cpu_cores = engine_config.get('cpu-cores', None)
        if cpu_cores:
            self.cpu_cores_will_change(cpu_cores)

        enable_web_ui = engine_config.get('enable-web-ui', None)
        if enable_web_ui:
            if isinstance(enable_web_ui, bool):
                self.enable_web_ui = enable_web_ui
            else:
                print('engine: enable-web-ui parameter should be a boolean')
        change_detection_root = engine_config.get('change-detection-root', None)
        if change_detection_root:
            if isinstance(change_detection_root, str):
                self.change_detection_root = change_detection_root
            else:
                print('engine: change_detection_root parameter should be a string')
        multiprocess_threshold = engine_config.get('multiprocessing-threshold', None)
        if multiprocess_threshold:
            self.multiprocess_threshold_will_change(multiprocess_threshold)
        self.load_pytest_plugin_config(engine_config)
        self.load_module_prefixes_config(engine_config)
        self.load_function_prefixes_config(engine_config)
        # this is in seconds
        execution_timeout = engine_config.get('timeout', None)
        if execution_timeout is not None:
            self.execution_timeout_will_change(execution_timeout)
        self.deep_inheritance_will_change(engine_config)

    def configuration_file_path(self):
        return self.working_directory.joinpath(CONFIG_FILE_NAME)

    def runtime_mode_will_change(self, runtime_mode):
        self.throw_if_mode_not_supported(runtime_mode)
        print(
            f'Engine execution mode will change from {self.engine_mode} to {runtime_mode}'
        )
        self.engine_mode = runtime_mode

    def throw_if_mode_not_supported(self, runtime_mode):
        if runtime_mode not in self.allowed_modes:
            raise Exception(
                f"runtime mode {runtime_mode} not supported. Available options are: {self.allowed_modes}"
            )

    def load_pytest_plugin_config(self, engine_config):
        node: Optional[str] = engine_config.get('load-pytest-plugins', None)
        if node is not None:
            if isinstance(node, bool):
                self.load_pytest_plugins = node

    def load_module_prefixes_config(self, engine_config):
        node: Optional[str] = engine_config.get('module-prefixes', None)
        if node is not None:
            if isinstance(node, str):
                self.module_prefixes = node.split(' ')

    def load_function_prefixes_config(self, engine_config):
        node: Optional[str] = engine_config.get('function-prefixes', None)
        if node is not None:
            if isinstance(node, str):
                self.function_prefixes = node.split(' ')

    def deep_inheritance_will_change(self, engine_config):
        deep_inheritance: str = engine_config.get('deep-inheritance', None)
        if deep_inheritance is not None:
            if isinstance(deep_inheritance, bool):
                self.deep_inheritance = deep_inheritance

    def execution_timeout_will_change(self, new_timeout: float):
        if new_timeout < 0:
            logger.error(
                f'Execution timeout of {new_timeout} not valid. Fallback to default 60 sec. Please use positive numbers'
            )
            return

        print(
            f'Using custom execution timeout of {new_timeout} seconds (default - 60 seconds)'
        )
        self.execution_timeout_in_seconds = new_timeout

    def save_pinned_tests_config(self, fqns):
        self.apply_pinned_tests(fqns)
        existing_config = None
        with io.open(self.configuration_file_path(), encoding='utf-8', mode='r') as f:
            existing_config = yaml.safe_load(f)

        existing_config['pinned-tests'] = list(fqns)
        with io.open(self.configuration_file_path(), encoding='utf-8', mode='w') as f:
            yaml.dump(existing_config, f, default_flow_style=False)

    def is_test_pinned(self, fqn):
        return fqn in self.pinned_tests

    def apply_pinned_tests(self, pinned_tests):
        self.pinned_tests = set()
        for fqn in pinned_tests:
            self.pinned_tests.add(fqn)

    def apply_additional_env(self, additional_env):
        print('Using additional env from config:')
        print(additional_env)
        for env in additional_env:
            self.environment_vars[env] = additional_env[env]

        for env_name, env_value in self.environment_vars.items():
            environ[env_name] = env_value

    def apply_path_mapping(self, path_mapping):
        print('custom path map')
        for p in path_mapping:
            # only one for now
            self.path_mapping = PathMapping(p, path_mapping[p])

    def cpu_cores_will_change(self, cpu_cores):
        self.cpu_cores = cpu_cores
        pass

    def get_default_cpu_cores(self):
        cores = multiprocessing.cpu_count()
        if cores > 8:
            return 4

        if cores <= 2:
            return 1

        return round(cores / 2)

    def get_execution_timeout(self) -> Optional[float]:
        if self.execution_timeout_in_seconds == 0:
            return None
        return self.execution_timeout_in_seconds

    def multiprocess_threshold_will_change(self, multiprocessing_threshold):
        self.multiprocessing_threshold = multiprocessing_threshold

    def apply_coverage_exclusions(self, exclusions: Optional[List[str]]):
        if exclusions is None:
            return

        if not hasattr(exclusions, "__len__"):
            raise Exception(
                '.pycrunch-config.yaml: apply_coverage->exclusions should be array'
            )

        self.coverage_exclusions = list(
            (f'*{_}*' if not _.endswith('.py') else f'*{_}' for _ in exclusions)
        )


class _Lazy(object):
    _config_instance: Optional[Configuration]

    def __init__(self):
        self.download = None
        self._config_instance = None

    @property
    def config(self):
        if not self._config_instance:
            self._config_instance = Configuration()
        return self._config_instance

    def __getattr__(self, name):
        return self.config.__getattribute__(name)


config = _Lazy()  #  type: Optional[Configuration]
