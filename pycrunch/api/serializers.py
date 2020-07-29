from collections import OrderedDict

from pycrunch.session import config


class CoverageRunForSingleFile:
    def __init__(self, filename, lines):
        self.lines = lines
        self.filename = filename

    def as_json(self):
        return OrderedDict(filename=config.path_mapping.map_to_local_fs(self.filename), lines_covered=self.lines,)

class CoverageRun:
    def __init__(self, fqn, time_elapsed, test_metadata, execution_result):
        self.test_metadata = test_metadata
        self.time_elapsed = time_elapsed
        self.entry_point = fqn
        self.execution_result = execution_result
        self.percentage_covered = -1
        self.files = []

    def store_files_coverage(self, files):
        """
        :type files: typing.List[CoverageRunForSingleFile]
        """
        self.files = files



    def as_json(self):
        files_ = [x.as_json() for x in self.files]
        return dict(
            entry_point=self.entry_point,
            time_elapsed=round(self.time_elapsed * 1000, 2),
            test_metadata=self.test_metadata,
            files=files_,
            status=self.execution_result.status,
            captured_output=self.execution_result.captured_output,
            variables_state=self.execution_result.state_timeline.as_json(),
        )





def serialize_test_set_state(test_set):
    def serialize_test(test_state):
        """

        :type test_state: pycrunch.shared.models.TestState
        """
        discovered_test = test_state.discovered_test
        execution_result = test_state.execution_result
        return dict(
            fqn=discovered_test.fqn,
            module=discovered_test.module,
            filename=config.path_mapping.map_to_local_fs(discovered_test.filename),
            name=discovered_test.name,
            state=execution_result.status,
            pinned=test_state.pinned,
        )

    return dict(
        tests=[serialize_test(v) for (k, v) in test_set.items()],
        )