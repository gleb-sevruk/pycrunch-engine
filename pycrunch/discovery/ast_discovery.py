import ast
import logging
from pathlib import Path
from typing import List

from pycrunch.discovery.ast_module_parse import AstModule
from pycrunch.discovery.shared import AbstractTestDiscovery, TestsInModule, TestSet
from pycrunch.insights import trace
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup

from pycrunch.session.file_map import test_map

from pycrunch.session import config

logger = logging.getLogger(__name__)


class AstTestDiscovery(AbstractTestDiscovery):
    def __init__(self, root_directory=None, configuration=None):
        self.root_directory = root_directory
        self.configuration = configuration if configuration is not None else config

    def find_tests_in_folder(self, folder, search_only_in=None) -> TestSet:
        import glob, importlib, os, pathlib, sys

        MODULE_DIR = self.get_root_directory(folder)

        logger.debug(f'AST-> Discovering tests in folder {folder}')

        # fixme 1 begin
        # if not MODULE_DIR in sys.path:
        #     sys.path.insert(0, MODULE_DIR)
        #     logger.debug(f'after append')
        #     logger.debug(sys.path)
        # fixme 1 end

        parent_path = pathlib.Path(MODULE_DIR)
        folder_path = pathlib.Path(folder)

        py_files = folder_path.glob('**/*.py')
        test_set = TestSet()

        with ModuleCleanup() as cleanup:
            for py_file in py_files:

                if search_only_in:
                    if str(py_file) not in search_only_in:
                        continue

                current_file_path = py_file.relative_to(parent_path)
                if self.is_excluded_via_configuration(current_file_path):
                    continue

                module_name = self.compute_module_name_from_path(current_file_path)
                # module_name = pathlib.Path(py_file).stem
                if not self.is_module_with_tests(module_name):
                    continue

                try:
                    logger.warning('NOT importing; AST goes into the light...' + module_name)
                    # module = importlib.import_module(module_name)
                    tests_found = self.find_tests_in_module_via_ast(py_file)
                except Exception as ex:
                    logger.error(f'Failed to load `{current_file_path}`')
                    logger.exception(f'AST {module_name} failed with exception: ' + str(ex))
                    continue

                filename = str(py_file)

                test_map.did_found_tests_in_file(filename, tests_found, module_name)
                test_set.add_module(TestsInModule(filename, tests_found, module_name))

                logger.warning(f'tests found: {tests_found}')

        # todo should we mutate global state or return value?
        return test_set

    def find_tests_in_module_via_ast(self, py_file: Path) -> List[str]:
        return AstModule().get_names(py_file)

    def is_module_with_tests(self, module_name):
        module_short_name = module_name.split('.')[-1]
        return module_short_name.startswith(('test_', 'tests_')) or module_short_name.endswith(('_test', 'tests', '_tests'))

    def is_excluded_via_configuration(self, current_file_path):
        s = str(current_file_path)
        x = False
        if s.startswith(self.configuration.discovery_exclusions) or s.endswith(self.configuration.discovery_exclusions):
            x = True
        return x

    def compute_module_name_from_path(self, current_file_path):
        if len(current_file_path.parts) > 1:
            module_name = str.join('.', current_file_path.parts[:-1]) + '.' + current_file_path.stem
        else:
            module_name = current_file_path.stem

        return module_name

    def get_root_directory(self, folder):
        if not self.root_directory:
            MODULE_DIR = folder
        else:
            MODULE_DIR = self.root_directory
        return MODULE_DIR
