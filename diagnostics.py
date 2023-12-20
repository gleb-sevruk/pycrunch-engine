from pprint import pprint

from coverage import Coverage, CoverageData


def print_coverage(coverage_data: CoverageData, coverage: Coverage):
    for f in coverage_data.measured_files():
        lines = coverage_data.lines(f)
        print('')
        print('')
        pprint(f)
        print('lines:')
        pprint(lines)
        print('')
        print('arcs:')
        pprint(coverage_data.arcs(f))
        print('')
        print('')
        zzz = coverage.analysis(f)
        pprint(zzz)
        print('')
        print()

    summary = coverage_data.line_counts()
    print('line_counts')
    pprint(summary)
