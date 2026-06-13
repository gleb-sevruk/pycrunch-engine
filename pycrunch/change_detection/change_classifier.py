from dataclasses import dataclass
from typing import FrozenSet, NamedTuple, Optional

from pycrunch.change_detection.fingerprint import (
    FileFingerprint,
    FunctionFingerprint,
    compute_file_fingerprint,
)


@dataclass(frozen=True)
class ChangeKind:
    """Base for all classifier results."""


@dataclass(frozen=True)
class NoChange(ChangeKind):
    pass


@dataclass(frozen=True)
class BodyOnlyChange(ChangeKind):
    changed_functions: FrozenSet[
        FunctionFingerprint
    ]  # OLD fingerprints (old line ranges)
    added_functions: FrozenSet[str]  # qualnames new in this version


@dataclass(frozen=True)
class ModuleLevelChange(ChangeKind):
    pass


@dataclass(frozen=True)
class UnparseableChange(ChangeKind):
    pass


@dataclass(frozen=True)
class TestFileChange(ChangeKind):
    changed_tests: FrozenSet[str]  # qualnames of test functions with changed body
    changed_fixtures: FrozenSet[str]  # qualnames of fixtures with changed body
    changed_support_functions: FrozenSet[
        FunctionFingerprint
    ]  # OLD fingerprints of non-test/non-fixture functions
    # When skeleton_changed=True the caller re-runs all tests in the file; the granular
    # lists are still populated but are not required for correctness in that case.
    skeleton_changed: bool  # imports/constants/signatures/function set changed


class ClassificationResult(NamedTuple):
    kind: ChangeKind
    new_fp: Optional[FileFingerprint]


def function_body_did_change(
    old_fn: FunctionFingerprint, new_fn: FunctionFingerprint
) -> bool:
    return old_fn.body_hash != new_fn.body_hash


def _classify_test_file_change(
    old: Optional[FileFingerprint],
    new_fp: FileFingerprint,
) -> ClassificationResult:
    # Conservative when no old snapshot or old was built without test_file mode.
    # One-time migration: forces all tests to run on the first smart-mode edit.
    if old is None or not old.test_file:
        return ClassificationResult(
            TestFileChange(
                changed_tests=frozenset(),
                changed_fixtures=frozenset(),
                changed_support_functions=frozenset(),
                skeleton_changed=True,
            ),
            new_fp,
        )

    skeleton_changed = old.module_level_hash != new_fp.module_level_hash

    old_funcs = old.functions
    new_funcs = new_fp.functions
    all_qualnames = set(old_funcs) | set(new_funcs)

    changed_tests: list = []
    changed_fixtures: list = []
    changed_support_functions: list = []
    any_func_change = False

    for qn in all_qualnames:
        if qn in old_funcs and qn in new_funcs:
            if function_body_did_change(old_funcs[qn], new_funcs[qn]):
                old_fn = old_funcs[qn]
                any_func_change = True
                if old_fn.is_fixture:
                    changed_fixtures.append(qn)
                elif old_fn.is_test:
                    changed_tests.append(qn)
                else:
                    changed_support_functions.append(old_fn)
        # Added/deleted functions affect the skeleton, caught by skeleton_changed above.

    if not skeleton_changed and not any_func_change:
        return ClassificationResult(NoChange(), new_fp)

    return ClassificationResult(
        TestFileChange(
            changed_tests=frozenset(changed_tests),
            changed_fixtures=frozenset(changed_fixtures),
            changed_support_functions=frozenset(changed_support_functions),
            skeleton_changed=skeleton_changed,
        ),
        new_fp,
    )


def classify_file_change(
    old: Optional[FileFingerprint],
    new_source: str,
    filename: str,
    *,
    root: Optional[str] = None,
    test_file: bool = False,
) -> ClassificationResult:
    """Classify the change between old fingerprint and new_source."""
    try:
        new_fp = compute_file_fingerprint(
            new_source, filename, root, test_file=test_file
        )
    except SyntaxError:
        return ClassificationResult(UnparseableChange(), None)

    if test_file:
        return _classify_test_file_change(old, new_fp)

    # Non-test-file logic (M1-M6 unchanged)
    if old is None:
        return ClassificationResult(ModuleLevelChange(), new_fp)

    if old.module_level_hash != new_fp.module_level_hash:
        return ClassificationResult(ModuleLevelChange(), new_fp)

    old_funcs = old.functions
    new_funcs = new_fp.functions

    changed: list = []
    added: list = []

    all_qualnames = set(old_funcs) | set(new_funcs)
    for qn in all_qualnames:
        if qn in old_funcs and qn in new_funcs:
            if function_body_did_change(old_funcs[qn], new_funcs[qn]):
                changed.append(old_funcs[qn])  # OLD fingerprint with old line ranges
        elif qn in new_funcs:
            added.append(qn)
        else:
            # deleted — add old fingerprint so its tests get re-run
            changed.append(old_funcs[qn])

    if not changed and not added:
        return ClassificationResult(NoChange(), new_fp)

    return ClassificationResult(
        BodyOnlyChange(
            changed_functions=frozenset(changed),
            added_functions=frozenset(added),
        ),
        new_fp,
    )
