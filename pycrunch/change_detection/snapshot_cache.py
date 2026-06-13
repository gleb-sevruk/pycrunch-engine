from typing import Dict, Optional, Set

from pycrunch.change_detection import normalize_path
from pycrunch.change_detection.fingerprint import FileFingerprint


class FileSnapshotCache:
    def __init__(self):
        # key: normalize_path(absolute_filename)  value: FileFingerprint
        self._snapshots: Dict[str, FileFingerprint] = {}

    def get(self, filename: str) -> Optional[FileFingerprint]:
        return self._snapshots.get(normalize_path(filename))

    def update(self, filename: str, fp: FileFingerprint) -> None:
        self._snapshots[normalize_path(filename)] = fp

    def remove(self, filename: str) -> None:
        self._snapshots.pop(normalize_path(filename), None)

    def known_files(self) -> Set[str]:
        return set(self._snapshots.keys())


snapshot_cache = FileSnapshotCache()
