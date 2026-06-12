from pathlib import Path
from typing import Set


def normalize_path(p: str) -> str:
    return str(Path(p).resolve())


def match_fqns(qualname: str, candidates) -> Set[str]:
    """Map a function qualname to matching test FQNs.

    FQN format:      'module_name:test_name'
    qualname format: 'test_foo' (top-level) or 'TestClass.test_method' (class method)
    FQN name part for class methods: 'TestClass::test_method'
    Also matches parametrized variants: 'module:test_a[1]' when qualname is 'test_a'.
    """
    test_name = qualname.replace('.', '::')
    result = set()
    for fqn in candidates:
        _, _, name_part = fqn.partition(':')
        if name_part == test_name or name_part.startswith(test_name + '['):
            result.add(fqn)
    return result
