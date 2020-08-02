import inspect
import logging
import sys

from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.session import config
from pycrunch.session.file_map import test_map

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
        self.files = set()
        self.tests = []

    def add_module(self, tests_in_module):
        self.files.add(tests_in_module.filename)
        for test in tests_in_module.tests_found:
            self.tests.append(DiscoveredTest(test, tests_in_module.filename, tests_in_module.module))


class TestsInModule:
    def __init__(self, filename, tests_found, module):
        # list of raw strings
        self.tests_found = tests_found
        self.filename = filename
        self.module = module




class SimpleTestDiscovery:

    def __init__(self, root_directory=None, configuration=None):
        self.root_directory = root_directory
        self.configuration = configuration if configuration is not None else config

    def find_tests_in_folder(self, folder, search_only_in = None):

        import glob, importlib, os, pathlib, sys

        if not self.root_directory:
            MODULE_DIR = folder
        else:
            MODULE_DIR = self.root_directory

        logger.debug(sys.path)
        logger.debug(f'MODULE_DIR {MODULE_DIR}')
        logger.debug(f'Discovering tests in folder {folder}')

        if not MODULE_DIR in sys.path:
            sys.path.insert(0, MODULE_DIR)
            logger.debug(f'after append')
            logger.debug(sys.path)
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
        from os import environ
        for env_name, env_value in config.environment_vars.items():
            environ[env_name] = env_value

        self.configuration.prepare_django()
        with ModuleCleanup() as cleanup:

            for py_file in py_files:

                if search_only_in:
                    if str(py_file) not in search_only_in:
                        continue


                # print(py_file)
                current_file_path = py_file.relative_to(parent_path)
                if self.is_excluded_via_configuration(current_file_path):
                    continue

                module_name = self.compute_module_name_from_path(current_file_path)
                # module_name = pathlib.Path(py_file).stem
                if not self.is_module_with_tests(module_name):
                    continue
                try:
                    logger.warning('importing ' + module_name)
                    module = importlib.import_module(module_name)
                    tests_found = self.find_tests_in_module(module)
                except Exception as ex:
                    logger.error(f'Failed to load `{current_file_path}`')
                    logger.exception(f'importing {module_name} failed with exception: ' + str(ex))
                    continue
                # execute as following
                # method_to_call = getattr(module, 'test_1')

                filename = str(py_file)

                test_map.did_found_tests_in_file(filename, tests_found, module_name)
                test_set.add_module(TestsInModule(filename, tests_found, module_name))

                logger.warning(f'tests found: {tests_found}')

        # todo should we mutate global state or return value?
        return test_set

    def compute_module_name_from_path(self, current_file_path):
        if len(current_file_path.parts) > 1:
            module_name = str.join('.', current_file_path.parts[:-1]) + '.' + current_file_path.stem
        else:
            module_name = current_file_path.stem
        return module_name

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

            if self.is_subclass_of_unittest(function_or_variable_or_class):
                # print(f'{v} : {function_or_variable_or_class} issubclass of unittest')
                attr = getattr(function_or_variable_or_class, "__test__", True)
                # print(attr)
                names = self.get_test_case_names_from_class(function_or_variable_or_class)
                names = map(lambda _: v + '::' + _, names)
                found_methods.extend(names)
                continue

            if self.looks_like_test_name(v):
                function_or_variable_or_class = getattr(module, v)
                if callable(function_or_variable_or_class):
                    found_methods.append(v)
        return found_methods

    def is_subclass_of_unittest(self, function_or_variable_or_class):
        is_class = inspect.isclass(function_or_variable_or_class)
        if not is_class:
            return False

        may_be_not_loaded = sys.modules.get("unittest")
        is_unit_test_sub = may_be_not_loaded and issubclass(function_or_variable_or_class, may_be_not_loaded.TestCase)
        return is_unit_test_sub

    def is_module_with_tests(self, module_name):
        module_short_name = module_name.split('.')[-1]
        return module_short_name.startswith(('test_', 'tests_')) or module_short_name.endswith(('_test','tests', '_tests'))

    def looks_like_test_name(self, v):
        return v.startswith('test_') or v.endswith('_test')

    def get_test_case_names_from_class(self, test_case_class):
        # implementation from standard unitest library
        def is_test_method_in_class(attrname, test_case_class_2=test_case_class):
            startswith = self.looks_like_test_name(attrname)
            can_call = callable(getattr(test_case_class_2, attrname))
            return startswith and can_call

        return list(filter(is_test_method_in_class, dir(test_case_class)))

 # for basecls in inspect.getmro(self.obj.__class__):
 #            dicts.append(basecls.__dict__)