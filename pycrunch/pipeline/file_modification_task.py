import platform
import time

from pycrunch.constants import CONFIG_FILE_NAME
from pycrunch.discovery.strategy import create_test_discovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.pipeline.config_reload_task import ConfigReloadTask
from pycrunch.pipeline.run_debouncing import RunDebouncer
from pycrunch.session import state
from pycrunch.session.combined_coverage import combined_coverage
from pycrunch.session.file_map import test_map


def is_running_on_m1():
    machine = platform.machine()
    return machine == "arm64" and platform.system() == "Darwin"


def get_debounce_delay():
    if is_running_on_m1():
        # This has higher memory bus and disk architecture,
        # we do not need to wait for that long.
        #  Also, lets give a user impression that M1 is faster.
        return 0.095
    return 0.185


run_debouncer = RunDebouncer(debounce_delay=get_debounce_delay())


class FileModifiedNotificationTask(AbstractTask):
    def __init__(self, file, context=None):
        self.file = file
        self.timestamp = time.time()
        self.context = context

    async def run(self):
        if self.file.endswith(CONFIG_FILE_NAME):
            execution_pipeline.add_task(ConfigReloadTask())
            return

        # look out for new tests in changed files
        # clean up zombie tests
        # run impacted tests and newly discovered
        # todo: Do not block event_loop!
        discovery = create_test_discovery()
        old_map = test_map.get_immutable_tests_for_file(self.file)
        possibly_new_tests = discovery.find_tests_in_folder(
            state.engine.folder, search_only_in=[self.file]
        )
        await state.engine.test_discovery_will_become_available(possibly_new_tests)

        new_map = test_map.get_immutable_tests_for_file(self.file)
        removed_tests = set()
        added_tests = set()
        for t in old_map:
            if t not in new_map:
                removed_tests.add(t)

        for t in new_map:
            if t not in old_map:
                added_tests.add(t)

        execution_plan = set()
        for new_test in possibly_new_tests.tests:
            if new_test.fqn in new_map:
                execution_plan.add(new_test.fqn)

        dependencies = combined_coverage.dependencies
        if dependencies:
            impacted_tests = dependencies[self.file]

            for fqn in impacted_tests:
                if fqn not in removed_tests:
                    execution_plan.add(fqn)
                else:
                    print(f"test {fqn} removed from execution plan")

            if state.config.engine_mode == 'manual':
                print(
                    'Manual mode, tests wont run. Consider switching engine mode to auto'
                )
                return

            tests_to_run = state.engine.all_tests.collect_by_fqn(execution_plan)
            dirty_tests = self.consider_engine_mode(tests_to_run)
            run_debouncer.add_tests(dirty_tests)
            await run_debouncer.schedule_run()

    def consider_engine_mode(self, tests_to_run):
        if state.config.engine_mode == 'auto':
            return tests_to_run

        if state.config.engine_mode == 'pinned':
            only_pinned = []
            for test in tests_to_run:
                if test.pinned:
                    only_pinned.append(test)
            return only_pinned
        print('Cannot filter by engine mode.')
        return tests_to_run


# https://stackoverflow.com/questions/45369128/python-multithreading-queue
