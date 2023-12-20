import os


def normalize_path(possible_relative_path: str) -> str:
    return os.path.normpath(os.path.realpath(possible_relative_path))
