
import logging
import os

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

    def __init__(self, root_directory=None):
        self.root_directory = root_directory

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
            current_file_path = py_file.relative_to(parent_path)
            if len(current_file_path.parts) > 1:
                module_name = str.join('.', current_file_path.parts[:-1]) + '.' + current_file_path.stem
            else:
                module_name = current_file_path.stem
            # module_name = pathlib.Path(py_file).stem
            if not self.is_module_with_tests(module_name):
                continue

            module = importlib.import_module(module_name)
            tests_found = self.find_tests_in_module(module)
            # execute as following
            # method_to_call = getattr(module, 'test_1')

            # http://forums.cgsociety.org/t/proper-way-of-reloading-a-python-module-with-new-code-without-having-to-restart-maya/1648174/8
            del sys.modules[module_name]

            test_set.add_module(TestsInModule(str(py_file), tests_found, module_name))

            logger.warning(f'tests found: {tests_found}')


        return test_set

    def find_tests_in_module(self, module):
        all_methods = dir(module)
        found_methods = []
        for m in all_methods:
            if m.startswith('test_') or m.endswith('_test'):
                found_methods.append(m)
        return found_methods


    def is_module_with_tests(self, module_name):
        module_short_name = module_name.split('.')[-1]
        return module_short_name.startswith('tests_') or module_short_name.endswith('_tests')
