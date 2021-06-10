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


class AbstractTestDiscovery:
    def find_tests_in_folder(self, folder, search_only_in = None) -> TestSet:
        raise Exception('Abstract method call in AbstractTestDiscovery->find_tests_in_folder')

