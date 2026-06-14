import asyncio
import functools
import logging
import os
import platform
import time
from pathlib import Path
from typing import Optional, Set

import pycrunch.change_detection.import_graph as _ig_mod
import pycrunch.change_detection.snapshot_cache as _sc_mod
import pycrunch.session.combined_coverage as _cc_mod
import pycrunch.session.file_map as _fm_mod
from pycrunch.change_detection import find_fqns_for_qualname, normalize_path
from pycrunch.change_detection.change_classifier import (
    BodyOnlyChange,
    ModuleLevelChange,
    NoChange,
    TestFileChange,
    UnparseableChange,
    classify_file_change,
)
from pycrunch.constants import CONFIG_FILE_NAME
from pycrunch.discovery.strategy import create_test_discovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.pipeline.config_reload_task import ConfigReloadTask
from pycrunch.pipeline.run_debouncing import RunDebouncer
from pycrunch.session import state

logger = logging.getLogger(__name__)

_UNSET = object()  # sentinel: old_fp not explicitly passed by caller


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
        # look out for new tests in changed files
        # clean up zombie tests
        # run impacted tests and newly discovered
        if self.file.endswith(CONFIG_FILE_NAME):
            execution_pipeline.add_task(ConfigReloadTask())
            return

        # Capture snapshot BEFORE discovery, which will overwrite it with the new file version.
        _old_fp_before_discovery = _sc_mod.snapshot_cache.get(normalize_path(self.file))

        discovery = create_test_discovery()
        old_map = _fm_mod.test_map.get_immutable_tests_for_file(self.file)

        preserve = state.config.change_detection_mode == 'smart'
        possibly_new_tests = discovery.find_tests_in_folder(
            state.engine.folder, search_only_in=[self.file]
        )
        await state.engine.test_discovery_will_become_available(
            possibly_new_tests, preserve_state=preserve
        )

        new_map = _fm_mod.test_map.get_immutable_tests_for_file(self.file)
        removed_tests = set()
        added_tests = set()
        for t in old_map:
            if t not in new_map:
                removed_tests.add(t)
        for t in new_map:
            if t not in old_map:
                added_tests.add(t)

        execution_plan = set()

        if preserve:
            # Smart mode: only add genuinely new tests upfront; changed/unchanged
            # tests are handled by _smart_execution_plan.
            execution_plan |= added_tests
            smart_plan = await self._smart_execution_plan(
                removed_tests, _old_fp_before_discovery
            )
            execution_plan |= smart_plan

            if state.config.engine_mode == 'manual':
                logger.info(
                    'Manual mode, tests wont run. Consider switching engine mode to auto'
                )
                return

            if not execution_plan:
                logger.info(
                    'smart-detection: empty execution plan, skipping run scheduling'
                )
                return

            tests_to_run = state.engine.all_tests.collect_by_fqn(execution_plan)
            dirty_tests = self.consider_engine_mode(tests_to_run)
            run_debouncer.add_tests(dirty_tests)
            await run_debouncer.schedule_run()
        else:
            # Legacy mode: exact original structure preserved.
            for new_test in possibly_new_tests.tests:
                if new_test.fqn in new_map:
                    execution_plan.add(new_test.fqn)

            dependencies = _cc_mod.combined_coverage.dependencies
            if dependencies:
                impacted_tests = dependencies[self.file]
                for fqn in impacted_tests:
                    if fqn not in removed_tests:
                        execution_plan.add(fqn)

                if state.config.engine_mode == 'manual':
                    logger.info(
                        'Manual mode, tests wont run. Consider switching engine mode to auto'
                    )
                    return

                tests_to_run = state.engine.all_tests.collect_by_fqn(execution_plan)
                dirty_tests = self.consider_engine_mode(tests_to_run)
                run_debouncer.add_tests(dirty_tests)
                await run_debouncer.schedule_run()

    async def _smart_execution_plan(
        self, removed_tests: set, old_fp=_UNSET
    ) -> Set[str]:
        loop = asyncio.get_event_loop()
        filename = normalize_path(self.file)

        if self.is_conftest(filename):
            return self._conftest_plan(filename)

        # If called from run(), old_fp is pre-captured before discovery overwrote the cache.
        # If called directly (e.g. in tests), fall back to reading from cache.
        if old_fp is _UNSET:
            old_fp = _sc_mod.snapshot_cache.get(filename)

        try:
            new_source = await loop.run_in_executor(None, self._read_file, filename)
        except OSError:
            logger.warning(
                f'smart-detection: could not read {filename}, falling back to legacy'
            )
            return self._legacy_fallback()

        _classify = functools.partial(
            classify_file_change,
            root=state.config.change_detection_root,
        )
        kind, new_fp = await loop.run_in_executor(
            None, _classify, old_fp, new_source, filename
        )

        plan: Set[str] = set()

        if isinstance(kind, NoChange):
            logger.info(
                f'smart-detection: NoChange in {self.file} -> 0 tests scheduled'
            )

        elif isinstance(kind, TestFileChange):
            all_tests_in_file = set(
                _fm_mod.test_map.get_immutable_tests_for_file(filename)
            )

            if kind.skeleton_changed or kind.changed_fixtures:
                plan |= all_tests_in_file
                # Test files are usually not imported, but handle the edge case.
                if kind.skeleton_changed:
                    coverage = _cc_mod.combined_coverage
                    for importer in _ig_mod.import_graph.transitive_importers(filename):
                        plan |= coverage.dependencies.get(importer, set())
                        for fqn in _fm_mod.test_map.get_immutable_tests_for_file(
                            importer
                        ):
                            plan.add(fqn)
            else:
                # Precise: only changed test functions by qualname
                for qualname in kind.changed_tests:
                    plan |= find_fqns_for_qualname(qualname, all_tests_in_file)

                # Helpers: coverage-based lookup using old line ranges
                if kind.changed_support_functions:
                    coverage = _cc_mod.combined_coverage
                    stats = coverage.files.get(filename)
                    # TODO: PR145 - maybe there is more elegant way? what if function size dramatically changes across runs
                    # TODO: PR145 - I would rather not include this completely into code because its too much overhead
                    for fn in kind.changed_support_functions:
                        if stats is None:
                            plan |= all_tests_in_file
                            break
                        for line in range(fn.line_start, fn.line_end + 1):
                            plan |= stats.lines_with_entrypoints.get(line, set())

                # Safety fallback: qualname didn't match any FQN (convention mismatch)
                if not plan and kind.changed_tests:
                    logger.warning(
                        f'smart-detection: {len(kind.changed_tests)} changed test(s) in '
                        f'{self.file} matched 0 FQNs — falling back to all tests in file'
                    )
                    plan |= all_tests_in_file

            plan -= removed_tests
            logger.info(
                f'smart-detection: TestFileChange in {self.file} '
                f'(skeleton={kind.skeleton_changed}, fixtures={len(kind.changed_fixtures)}, '
                f'tests={len(kind.changed_tests)}) -> {len(plan)} tests scheduled'
            )

        elif isinstance(kind, BodyOnlyChange):
            coverage = _cc_mod.combined_coverage
            stats = coverage.files.get(filename)
            if stats is not None:
                for fn in kind.changed_functions:
                    for line in range(fn.line_start, fn.line_end + 1):
                        for fqn in stats.lines_with_entrypoints.get(line, set()):
                            if fqn not in removed_tests:
                                plan.add(fqn)
            if not plan:
                plan |= self._legacy_fallback(removed_tests)
            logger.info(
                f'smart-detection: BodyOnlyChange in {self.file} -> {len(plan)} tests scheduled'
            )

        elif isinstance(kind, ModuleLevelChange):
            plan |= self._legacy_fallback(removed_tests)
            coverage = _cc_mod.combined_coverage
            for importer in _ig_mod.import_graph.transitive_importers(filename):
                plan |= coverage.dependencies.get(importer, set())
                for fqn in _fm_mod.test_map.get_immutable_tests_for_file(importer):
                    plan.add(fqn)
            logger.info(
                f'smart-detection: ModuleLevelChange in {self.file} -> {len(plan)} tests scheduled'
            )

        elif isinstance(kind, UnparseableChange):
            plan |= self._legacy_fallback(removed_tests)
            logger.info(
                f'smart-detection: UnparseableChange in {self.file} -> {len(plan)} tests scheduled (legacy fallback)'
            )

        if new_fp is not None:
            _sc_mod.snapshot_cache.update(filename, new_fp)
            _ig_mod.import_graph.update_file(filename, new_fp)

        return plan

    def is_conftest(self, filename: str) -> bool:
        return Path(filename).name == 'conftest.py'

    def _legacy_fallback(self, removed_tests: Optional[set] = None) -> Set[str]:
        filename = normalize_path(self.file)
        coverage = _cc_mod.combined_coverage
        result = coverage.dependencies.get(filename, set())
        if removed_tests:
            result = {fqn for fqn in result if fqn not in removed_tests}
        return result

    def _conftest_plan(self, filename: str) -> Set[str]:
        conftest_parent = normalize_path(str(Path(filename).parent))
        dir_prefix = conftest_parent + os.sep
        plan: Set[str] = set()
        plan |= self._legacy_fallback()
        for test_file, fqns in _fm_mod.test_map.map.items():
            norm = normalize_path(test_file)
            if norm.startswith(dir_prefix):
                plan |= fqns
        logger.info(
            f'smart-detection: conftest change in {self.file} -> {len(plan)} tests scheduled'
        )
        return plan

    @staticmethod
    def _read_file(filename: str) -> str:
        with open(filename, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

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
