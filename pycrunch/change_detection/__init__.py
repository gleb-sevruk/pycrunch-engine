from pathlib import Path
from typing import Iterable, Set


def normalize_path(p: str) -> str:
    return str(Path(p).resolve())


def looks_like_test_class(name: str) -> bool:
    return name.startswith('Test') or name.endswith('Test')


def find_fqns_for_qualname(qualname: str, candidates: Iterable[str]) -> Set[str]:
    """Find all test FQNs whose name part matches qualname.

    qualname format: 'test_foo' (top-level) or 'TestClass.test_method' (class method).
    FQN format:      'module_name:test_name', class methods: 'module:TestClass::test_method'.
    Also matches parametrized variants: 'module:test_a[1]' when qualname is 'test_a'.
    Returns the matching subset from candidates.
    """
    test_name = qualname.replace('.', '::')
    result = set()
    for fqn in candidates:
        _, _, name_part = fqn.partition(':')
        if name_part == test_name or name_part.startswith(test_name + '['):
            result.add(fqn)
    return result
