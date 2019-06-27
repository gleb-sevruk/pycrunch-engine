import inspect
import logging
import os
import sys
from unittest.test import loader

from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.session import config

logger = logging.getLogger(__name__)


class DiscoveredTest:
    def __init__(self, name, filename, module):
        self.filename = filename
        self.module = module
        # name of the test
        self.name = name
        self.fqn = module + ':' + name

class TestSet:
    def __init__(self):
        self.modules = []
        self.tests = []

    def add_module(self, tests_in_module):
        self.modules.append(tests_in_module)
        for test in tests_in_module.tests_found:
            self.tests.append(DiscoveredTest(test, tests_in_module.filename, tests_in_module.module))


class TestsInModule:
    def __init__(self, filename, tests_found, module):
        self.tests_found = tests_found
        self.filename = filename
        self.module = module




class SimpleTestDiscovery:

    def __init__(self, root_directory=None, configuration=None):
        self.root_directory = root_directory
        self.configuration = configuration if configuration is not None else config

    def find_tests_in_folder(self, folder):
        import glob, importlib, os, pathlib, sys

        if not self.root_directory:
            MODULE_DIR = folder
        else:
            MODULE_DIR = self.root_directory

        print(sys.path)
        print(f'MODULE_DIR {MODULE_DIR}')

        sys.path.insert(0, MODULE_DIR)
        print(f'after append')
        print(sys.path)
        # The directory containing your modules needs to be on the search path.

        # Get the stem names (file name, without directory and '.py') of any
        # python files in your directory, load each module by name and run
        # the required function.

        parent_path = pathlib.Path(MODULE_DIR)
        folder_path = pathlib.Path(folder)
        # for x in folder_path.glob('**/*.py'):
        #     print('-')
        #     print(module_name_full)

        # py_files = glob.glob(os.path.join(folder, '*.py'))
        py_files = folder_path.glob('**/*.py')
        test_set = TestSet()
        for py_file in py_files:
            # print(py_file)
            current_file_path = py_file.relative_to(parent_path)
            if self.is_excluded_via_configuration(current_file_path):
                continue

            if len(current_file_path.parts) > 1:
                module_name = str.join('.', current_file_path.parts[:-1]) + '.' + current_file_path.stem
            else:
                module_name = current_file_path.stem
            # module_name = pathlib.Path(py_file).stem
            if not self.is_module_with_tests(module_name):
                continue

            with ModuleCleanup() as cleanup:
                module = importlib.import_module(module_name)
                tests_found = self.find_tests_in_module(module)
                # execute as following
                # method_to_call = getattr(module, 'test_1')

            test_set.add_module(TestsInModule(str(py_file), tests_found, module_name))

            logger.warning(f'tests found: {tests_found}')


        return test_set

    def is_excluded_via_configuration(self, current_file_path):
        s = str(current_file_path)
        x = False
        if s.startswith(self.configuration.discovery_exclusions) or s.endswith(self.configuration.discovery_exclusions):
            x = True
        return x

    def find_tests_in_module(self, module):
        all_variables = dir(module)
        found_methods = []
        for v in all_variables:
            function_or_variable_or_class = getattr(module, v)
            is_class = inspect.isclass(function_or_variable_or_class)
            if is_class and issubclass(function_or_variable_or_class, sys.modules["unittest"].TestCase):
                print(f'{v} : {function_or_variable_or_class} issubclass of unittest')
                attr = getattr(function_or_variable_or_class, "__test__", True)
                print(attr)
                names = self.get_test_case_names_from_class(function_or_variable_or_class)
                names = map(lambda _: v + '::' + _, names)
                found_methods.extend(names)
                continue

            if self.looks_like_test_name(v):
                function_or_variable_or_class = getattr(module, v)
                if callable(function_or_variable_or_class):
                    found_methods.append(v)
        return found_methods


    def is_module_with_tests(self, module_name):
        module_short_name = module_name.split('.')[-1]
        return module_short_name.startswith(('test_', 'tests_')) or module_short_name.endswith(('_test', '_tests'))

    def looks_like_test_name(self, v):
        return v.startswith('test_') or v.endswith('_test')

    def get_test_case_names_from_class(self, test_case_class):
        def is_test_method_in_class(attrname, test_case_class_2=test_case_class):
            startswith = self.looks_like_test_name(attrname)
            can_call = callable(getattr(test_case_class_2, attrname))
            return startswith and can_call

        return list(filter(is_test_method_in_class, dir(test_case_class)))

 # for basecls in inspect.getmro(self.obj.__class__):
 #            dicts.append(basecls.__dict__)