from typing import List, Optional

from pydantic import BaseModel


class DiscoveredTestModel(BaseModel):
    filename: str
    fqn: str
    module: str
    name: str
    pinned: Optional[bool] = None
    state: str


class FileCoverageModel(BaseModel):
    filename: str
    lines_covered: List[int]


class TestRunCompletedModel(BaseModel):
    __test__ = False
    time_elapsed: float
    test_metadata: DiscoveredTestModel
    captured_output: str
    files: List[FileCoverageModel]
    captured_exception: Optional[dict] = None
    variables_state: List[dict]
    entry_point: str
    status: str

    def find_file_by_suffix(self, suffix: str) -> Optional[FileCoverageModel]:
        for file in self.files:
            if file.filename.endswith(suffix):
                return file
        return None


class CombinedCoverage(BaseModel):
    filename: str
    lines_with_entrypoints: dict[str, List[str]]
    exceptions: List[dict]
