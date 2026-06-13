from typing import Dict, Optional, Set, Tuple

from pycrunch.change_detection import normalize_path
from pycrunch.change_detection.fingerprint import FileFingerprint


class FileSnapshotCache:
    def __init__(self):
        # key: normalize_path(absolute_filename)  value: (FileFingerprint, raw_source)
        self._snapshots: Dict[str, Tuple[FileFingerprint, str]] = {}

    def get(self, filename: str) -> Optional[FileFingerprint]:
        entry = self._snapshots.get(normalize_path(filename))
        return entry[0] if entry is not None else None

    def get_source(self, filename: str) -> Optional[str]:
        entry = self._snapshots.get(normalize_path(filename))
        return entry[1] if entry is not None else None

    def update(self, filename: str, fp: FileFingerprint, source: str = '') -> None:
        self._snapshots[normalize_path(filename)] = (fp, source)

    def remove(self, filename: str) -> None:
        self._snapshots.pop(normalize_path(filename), None)

    def known_files(self) -> Set[str]:
        return set(self._snapshots.keys())


snapshot_cache = FileSnapshotCache()
