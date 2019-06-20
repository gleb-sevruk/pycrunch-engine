import io
from collections import OrderedDict

from coverage import Coverage

from pycrunch.discovery.simple import DiscoveredTest


class CoverageRunForSingleFile:
    def __init__(self, filename, lines, arcs, analysis):
        self.analysis = analysis
        self.arcs = arcs
        self.lines = lines
        self.filename = filename

    def as_json(self):
        return OrderedDict(filename=self.filename, lines_covered=self.lines, analysis=self.analysis, arcs=self.arcs,)

class CoverageRun:
    def __init__(self, entry_point, time_elapsed, test_metadata, captured_output):
        self.test_metadata = test_metadata
        self.time_elapsed = time_elapsed
        self.entry_point = entry_point
        self.captured_output = captured_output
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
            time_elapsed=round(self.time_elapsed * 1000, 2),
            test_metadata=self.test_metadata,
            files=files_,
            captured_output=self.captured_output,
        )


def serialize_coverage(cov : Coverage, entry_file, time_elapsed, test_metadata, captured_output):
    run_results = CoverageRun(entry_file, time_elapsed, test_metadata, captured_output)
    run_results.parse_lines(cov)
    return run_results.as_json()


def serialize_test(discovered_test: DiscoveredTest):
    return dict(
        fqn=discovered_test.fqn,
        module=discovered_test.module,
        filename=discovered_test.filename,
        name=discovered_test.name,
        state='pending',
    )



def serialize_test_set(test_set):
    def serialize_module(tests_in_module):
        return dict(
            filename=tests_in_module.filename,
            tests_found=[dict(name=test_name, filename=tests_in_module.filename, module=tests_in_module.module) for test_name in tests_in_module.tests_found]
        )

    return dict(
        tests=[serialize_test(t) for t in test_set.tests],
        grouped=[serialize_module(m) for m in test_set.modules])