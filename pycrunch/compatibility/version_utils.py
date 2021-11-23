from typing import Tuple


def parse_version_string(v: str) -> Tuple:
    """
    "2.4" --> (1, 2, 0)
    "2" --> (2, 0, 0)
    """
    parts = v.split(".")
    parts = (parts + 3 * ["0"])[:3]
    return tuple(int(x) for x in parts)
