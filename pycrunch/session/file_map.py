import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


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
        if filename not in self.map:
            logger.info(
                f'file_did_removed could not find  {filename}. Probably it was removed earlier.'
            )
            return
        self.map.pop(filename)

    def test_exist(self, filename, fqn):
        if fqn in self.map[filename]:
            return True

        return False


test_map = TestMap()
