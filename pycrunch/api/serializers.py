import io
from collections import OrderedDict

from coverage import Coverage


class CoverageRunForSingleFile:
    def __init__(self, filename, lines, arcs, analysis):
        self.analysis = analysis
        self.arcs = arcs
        self.lines = lines
        self.filename = filename

    def as_json(self):
        return OrderedDict(filename=self.filename, lines_covered=self.lines, analysis=self.analysis, arcs=self.arcs,)

class CoverageRun:
    def __init__(self, entry_point):
        self.entry_point = entry_point
        self.percentage_covered = -1
        self.files = []


    def parse_lines(self, cov):
        output_file = io.StringIO()
        self.percentage_covered = round(cov.report(file=output_file), 2)
        coverage_data = cov.get_data()

        for f in coverage_data.measured_files():
            lines = coverage_data.lines(f)
            arcs = coverage_data.arcs(f)
            analysis = cov.analysis2(f)
            self.files.append(CoverageRunForSingleFile(f, lines, arcs, analysis))

    def as_json(self):
        files_ = [x.as_json() for x in self.files]
        return dict(
            percentage_covered=self.percentage_covered,
            entry_point=self.entry_point,
            files=files_,
        )


def serialize_coverage(cov : Coverage, entry_file):
    run_results = CoverageRun(entry_file)
    run_results.parse_lines(cov)
    return run_results.as_json()

def serialize_test_set(test_set):
    def serialize_module(tests_in_module):
        return dict(
            filename=tests_in_module.filename,
            tests_found=[test_name for test_name in tests_in_module.tests_found]
        )

    return [serialize_module(m) for m in test_set.modules]