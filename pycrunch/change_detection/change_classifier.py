from dataclasses import dataclass
from typing import FrozenSet, Optional, Sequence, Tuple, Union

from pycrunch.change_detection.fingerprint import (
    FileFingerprint,
    FunctionFingerprint,
    fingerprint_source,
)


@dataclass(frozen=True)
class NoChange:
    pass


@dataclass(frozen=True)
class BodyOnlyChange:
    changed_functions: FrozenSet[
        FunctionFingerprint
    ]  # OLD fingerprints (old line ranges)
    added_functions: FrozenSet[str]  # qualnames new in this version


@dataclass(frozen=True)
class ModuleLevelChange:
    pass


@dataclass(frozen=True)
class UnparseableChange:
    pass


@dataclass(frozen=True)
class TestFileChange:
    changed_tests: FrozenSet[str]  # qualnames of test functions with changed body
    changed_fixtures: FrozenSet[str]  # qualnames of fixtures with changed body
    changed_helpers: FrozenSet[
        FunctionFingerprint
    ]  # OLD fingerprints of non-test/non-fixture functions
    skeleton_changed: bool  # imports/constants/signatures/function set changed


ChangeKind = Union[
    NoChange, BodyOnlyChange, ModuleLevelChange, UnparseableChange, TestFileChange
]


def _classify_test_file(
    old: Optional[FileFingerprint],
    new_fp: FileFingerprint,
) -> Tuple[ChangeKind, Optional[FileFingerprint]]:
    # Conservative when no old snapshot or old was built without test_file mode.
    # One-time migration: forces all tests to run on the first smart-mode edit.
    if old is None or not old.test_file:
        return TestFileChange(
            changed_tests=frozenset(),
            changed_fixtures=frozenset(),
            changed_helpers=frozenset(),
            skeleton_changed=True,
        ), new_fp

    skeleton_changed = old.module_level_hash != new_fp.module_level_hash

    old_funcs = old.functions
    new_funcs = new_fp.functions
    all_qualnames = set(old_funcs) | set(new_funcs)

    changed_tests: list = []
    changed_fixtures: list = []
    changed_helpers: list = []
    any_func_change = False

    for qn in all_qualnames:
        if qn in old_funcs and qn in new_funcs:
            if old_funcs[qn].body_hash != new_funcs[qn].body_hash:
                old_fn = old_funcs[qn]
                any_func_change = True
                if old_fn.is_fixture:
                    changed_fixtures.append(qn)
                elif old_fn.is_test:
                    changed_tests.append(qn)
                else:
                    changed_helpers.append(old_fn)
        # Added/deleted functions affect the skeleton, caught by skeleton_changed above.

    if not skeleton_changed and not any_func_change:
        return NoChange(), new_fp

    return TestFileChange(
        changed_tests=frozenset(changed_tests),
        changed_fixtures=frozenset(changed_fixtures),
        changed_helpers=frozenset(changed_helpers),
        skeleton_changed=skeleton_changed,
    ), new_fp


def classify(
    old: Optional[FileFingerprint],
    new_source: str,
    filename: str,
    root: Optional[str] = None,
    test_file: bool = False,
    function_prefixes: Sequence[str] = ('test_',),
) -> Tuple[ChangeKind, Optional[FileFingerprint]]:
    try:
        new_fp = fingerprint_source(
            new_source,
            filename,
            root,
            test_file=test_file,
            function_prefixes=function_prefixes,
        )
    except SyntaxError:
        return UnparseableChange(), None

    if test_file:
        return _classify_test_file(old, new_fp)

    # Non-test-file logic (M1-M6 unchanged)
    if old is None:
        return ModuleLevelChange(), new_fp

    if old.module_level_hash != new_fp.module_level_hash:
        return ModuleLevelChange(), new_fp

    old_funcs = old.functions
    new_funcs = new_fp.functions

    changed: list = []
    added: list = []

    all_qualnames = set(old_funcs) | set(new_funcs)
    for qn in all_qualnames:
        if qn in old_funcs and qn in new_funcs:
            if old_funcs[qn].body_hash != new_funcs[qn].body_hash:
                changed.append(old_funcs[qn])  # OLD fingerprint with old line ranges
        elif qn in new_funcs:
            added.append(qn)
        else:
            # deleted — add old fingerprint so its tests get re-run
            changed.append(old_funcs[qn])

    if not changed and not added:
        return NoChange(), new_fp

    return BodyOnlyChange(
        changed_functions=frozenset(changed),
        added_functions=frozenset(added),
    ), new_fp
