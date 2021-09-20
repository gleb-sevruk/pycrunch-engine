from collections import defaultdict

class MethodDefinition:
    def __init__(self, name, start_line, end_line):
        self.name = name
        self.start_line = start_line
        self.end_line = end_line

    def is_in_range(self, line_to_check):
        return line_to_check >= self.start_line and line_to_check <= self.end_line

    def is_same(self, another_method):
        return self.name == another_method.name and \
               self.start_line == another_method.start_line and \
               self.end_line == another_method.end_line


class MethodMapForSingleFile:
    def __init__(self, filename):
        self.filename = filename
        # (method fqn) -> MethodDefinition
        self.methods = dict()

    def get_affected_methods(self, covered_lines):
        # covered_lines = array[1, 2, 5, 6] from coverage.py

        # returns array of methods
        methods_in_current_file = self.methods.values()
        method_names = set()
        # todo this is really suboptimal. Needs interval tree or fast-search data structure
        for line in covered_lines:
            for method in methods_in_current_file:
                if method.is_in_range(line):
                    method_names.add(method.name)
                    break
        return sorted(list(method_names))
        pass

    def compare_with_snapshot(self, another_method_map):
        results = list()
        for key,value in self.methods.items():
            print(key)
            another = another_method_map.methods.get(key, None)
            if not another:
                results.append(key)
            if not value.is_same(another):
                results.append(key)

        return results
        pass


class FilesMethodMap:
    def __init__(self):

        # filename -> [method_a, method_b, ...]
        # filename -> MethodMapForSingleFile

        self.methods_by_file = dict()
        pass


    def parse_file(self, filename):
        pass

    def get_affected_methods(self, filename, covered_lines):
        # covered_lines = array[1, 2, 5, 6] from coverage.py

        # returns array of methods
        methods_in_current_file = self.methods_by_file[filename]

        return methods_in_current_file.get_affected_methods(covered_lines)
        pass
