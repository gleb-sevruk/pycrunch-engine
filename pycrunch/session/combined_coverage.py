from collections import namedtuple, defaultdict
from pprint import pprint

from pycrunch.api.shared import file_watcher

FileWithCoverage = namedtuple('FileWithCoverage', ['filename', 'lines_covered', 'analysis', 'arcs'])

class FileStatistics:
    def __init__(self, filename):
        self.filename = filename
        self.lines_with_entrypoints = defaultdict(set)

    def mark_lines(self, lines_covered, by_entry_point):
        for possibly_oudated_line in self.lines_with_entrypoints:
            self.lines_with_entrypoints[possibly_oudated_line].discard(by_entry_point)

        for line in lines_covered:
            self.lines_with_entrypoints[line].add(by_entry_point)



class CombinedCoverage:
    """
        files[] -> line 1 -> [test1, test2]
                   line 2 -> [test2]
    """
    def __init__(self):
        self.files = dict()
        self.dependencies = defaultdict(list)
        pass

    def mark_dependency(self, filename, test_metadata):
        if test_metadata not in self.dependencies[filename]:
            self.dependencies[filename].append(test_metadata)

    def mark_coverage(self, entry_point, filename, lines_covered):
        if not filename in self.files:
            statistics = FileStatistics(filename=filename)
            self.files[filename] = statistics
        statistics = self.files[filename]
        statistics.mark_lines(lines_covered=lines_covered, by_entry_point=entry_point)

    def add_multiple_results(self, results):
        # todo invalidate\remove outdated runs

        for entry_point, test_run in results.items():
            for file in test_run['files']:
                file_with_coverage = FileWithCoverage(**file)
                self.mark_dependency(file_with_coverage.filename, test_run['test_metadata'])

                self.mark_coverage(entry_point=entry_point, filename=file_with_coverage.filename, lines_covered=file_with_coverage.lines_covered)

        file_watcher.watch(self.files.keys())

        # pprint(results)
        for x in self.files.values():
            pprint(x.filename)
            pprint(x.lines_with_entrypoints)
        pass

    def add_test_result(self, module, test_name, coverage):
        self.state[module + '.' + test_name] = coverage


combined_coverage = CombinedCoverage()