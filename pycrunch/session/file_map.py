from collections import defaultdict


class TestMap:
    def __init__(self):
        # filename -> test_fqn[]
        self.map = defaultdict(set)

    def did_found_tests_in_file(self, filename, test_names, module_name):
        if len(test_names) <= 0:
            return

        new_list = set()
        for test in test_names:
            new_list.add(module_name + ':' + test)

        self.map[filename] = new_list

    def get_immutable_tests_for_file(self, filename):
        return list(self.map.get(filename, set()))

    def file_did_removed(self, filename):
        self.map.pop(filename)

    def test_exist(self, filename, fqn):
        if fqn in self.map[filename]:
            return True

        return False


test_map = TestMap()