from collections import defaultdict
from pathlib import Path
from typing import Dict, FrozenSet, Optional, Set

from pycrunch.change_detection import normalize_path
from pycrunch.change_detection.fingerprint import FileFingerprint


def _file_to_module(filename: str, root: Optional[str]) -> str:
    try:
        path = Path(filename).resolve()
        if root:
            root_path = Path(root).resolve()
            rel = path.relative_to(root_path)
        else:
            return path.stem

        parts = list(rel.parts)
        if parts and parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]
        return '.'.join(parts) if parts else path.stem
    except (ValueError, Exception):
        return Path(filename).stem


class ImportGraph:
    def __init__(self, root: Optional[str] = None):
        self._root = root
        # module_name -> set of filenames that import it
        self._importers_by_module: Dict[str, Set[str]] = defaultdict(set)
        # filename -> module_name
        self._module_of_file: Dict[str, str] = {}
        # filename -> import_targets (for incremental updates)
        self._targets_of_file: Dict[str, FrozenSet[str]] = {}
        # module_name -> filename (reverse of _module_of_file)
        self._file_of_module: Dict[str, str] = {}

    def update_file(self, filename: str, fp: FileFingerprint) -> None:
        filename = normalize_path(filename)
        module_name = _file_to_module(filename, self._root)

        # remove old edges from this file
        old_targets = self._targets_of_file.get(filename, frozenset())
        for t in old_targets:
            self._importers_by_module[t].discard(filename)

        # register this file's module name
        old_module = self._module_of_file.get(filename)
        if old_module and old_module != module_name:
            self._file_of_module.pop(old_module, None)
        self._module_of_file[filename] = module_name
        self._file_of_module[module_name] = filename

        # add new edges
        self._targets_of_file[filename] = fp.import_targets
        for t in fp.import_targets:
            self._importers_by_module[t].add(filename)

    def remove_file(self, filename: str) -> None:
        filename = normalize_path(filename)
        old_targets = self._targets_of_file.pop(filename, frozenset())
        for t in old_targets:
            self._importers_by_module[t].discard(filename)

        module_name = self._module_of_file.pop(filename, None)
        if module_name:
            self._file_of_module.pop(module_name, None)

        # also remove this file as a target
        for s in self._importers_by_module.values():
            s.discard(filename)

    def transitive_importers(self, filename: str, max_depth: int = 20) -> Set[str]:
        filename = normalize_path(filename)
        module_name = self._module_of_file.get(filename)
        if not module_name:
            return set()

        visited_files: Set[str] = set()
        queue = [filename]
        depth = 0

        while queue and depth < max_depth:
            depth += 1
            next_queue = []
            for f in queue:
                mod = self._module_of_file.get(f)
                if not mod:
                    continue
                for importer in list(self._importers_by_module.get(mod, set())):
                    if importer not in visited_files and importer != filename:
                        visited_files.add(importer)
                        next_queue.append(importer)
            queue = next_queue

        return visited_files


import_graph = ImportGraph()
