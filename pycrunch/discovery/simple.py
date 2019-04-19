
import logging
import os

logger = logging.getLogger(__name__)


class TestSet:
    def __init__(self):
        self.modules = []

    def add_module(self, tests_in_module):
        self.modules.append(tests_in_module)


class TestsInModule:
    def __init__(self, filename, tests_found):
        self.tests_found = tests_found
        self.filename = filename



class SimpleTestDiscovery:
    def find_tests_in_folder(self, folder):
        import glob, importlib, os, pathlib, sys

        # The directory containing your modules needs to be on the search path.
        MODULE_DIR = folder
        sys.path.append(MODULE_DIR)

        # Get the stem names (file name, without directory and '.py') of any
        # python files in your directory, load each module by name and run
        # the required function.
        py_files = glob.glob(os.path.join(MODULE_DIR, '*.py'))
        test_set = TestSet()
        for py_file in py_files:
            # todo recursive ?
            module_name = pathlib.Path(py_file).stem
            if not self.is_module_with_tests(module_name):
                continue

            module = importlib.import_module(module_name)
            tests_found = self.find_tests_in_module(module)
            # execute as following
            # method_to_call = getattr(module, 'test_1')

            # http://forums.cgsociety.org/t/proper-way-of-reloading-a-python-module-with-new-code-without-having-to-restart-maya/1648174/8
            del sys.modules[module_name]

            test_set.add_module(TestsInModule(py_file, tests_found))

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
        return module_name.startswith('tests_') or module_name.endswith('_tests')
