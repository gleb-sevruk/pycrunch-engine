"""
This module is used to run pytest in a child process without need of full chain
"""
from pprint import pprint

from pycrunch.child_runtime.pytest_aware_runner.pytest_aware_runner import (
    PytestAwareTestRunner,
)
from pycrunch.child_runtime.test_runner import TestRunner
from pycrunch.plugins.pytest_support.pytest_runner_engine import PyTestRunnerEngine

tests_to_run = [
    # {
    #     "fqn": "pycrunch.tests.slow_simulated.test_generated:test_7528",
    #     "filename": "/Users/gleb/code/pycrunch-engine/pycrunch/tests/slow_simulated/test_generated.py",
    #     "name": "test_7528",
    #     "module": "pycrunch.tests.slow_simulated.test_generated",
    #     "state": "converted",
    # },
    # {
    #     "fqn": "pycrunch.tests.slow_simulated.test_generated:test_7529",
    #     "filename": "/Users/gleb/code/pycrunch-engine/pycrunch/tests/slow_simulated/test_generated.py",
    #     "name": "test_7529",
    #     "module": "pycrunch.tests.slow_simulated.test_generated",
    #     "state": "converted",
    # },
    # {
    #     "filename": "/Users/gleb/code/pycrunch-engine/pycrunch/tests/test_coverage_hal.py",
    #     "fqn": "pycrunch.tests.test_coverage_hal:TestCoverageRun::test_if_nothing_in_lines_do_not_add_file",
    #     "module": "pycrunch.tests.test_coverage_hal",
    #     "name": "TestCoverageRun::test_if_nothing_in_lines_do_not_add_file",
    #     "state": "converted",
    # },
    {
        "filename": "/Users/gleb/code/pycrunch-engine/pycrunch/tests/slow_simulated/test_generated.py",
        "fqn": "pycrunch.tests.slow_simulated.test_generated:test_758",
        "module": "pycrunch.tests.slow_simulated.test_generated",
        "name": "test_758",
        "state": "converted",
    },
]

from pycrunch.introspection.timings import Timeline
from pycrunch.child_runtime.child_config import child_config
from pprintpp import pprint as pp


def main():
    timeline = Timeline("multiprocess run engine")
    timeline.start()
    timeline.mark_event("__main__")
    child_config.enable_remote_debug = True
    # This line will enalbe coverage
    # child_config.enable_remote_debug = False
    test_runner = PytestAwareTestRunner(timeline, ["adittional_excludes"], child_config)
    results = test_runner.run(tests_to_run)
    for k, v in results.items():
        pp(k)
        # pprint(v.as_json())
    # import pydevd_pycharm
    # pydevd_pycharm.settrace('localhost', port=50147, stdoutToServer=True, stderrToServer=True)
    print("done")


if __name__ == "__main__":
    main()
