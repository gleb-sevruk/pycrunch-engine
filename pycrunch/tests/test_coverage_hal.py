import unittest
from unittest.mock import MagicMock
from pycrunch.child_runtime.coverage_hal import CoverageAbstraction
import pytest

class TestCoverageRun(unittest.TestCase):
    def test_if_nothing_in_lines_do_not_add_file(self):
        # Arrange
        cov_mock = MagicMock()
        your_instance = CoverageAbstraction(False, [], None)
        your_instance.cov = cov_mock
        # Set up the MagicMock to return desired values
        measured_files = ['/some/file1.py', '/some/file2.py', '/some/file_to_skip.py']
        lines_data = {
            '/some/file1.py': [1, 2, 3],
            '/some/file2.py': [4, 5, 6],
            '/some/file_to_skip.py': []
        }

        cov_mock.get_data.return_value.measured_files.return_value = measured_files
        cov_mock.get_data.return_value.lines.side_effect = lambda f: lines_data[f]

        # Act
        results = your_instance.parse_all_hit_lines()

        # Assert
        assert isinstance(results, list)
        assert len(results) == 2, "Third file should be not included as there is no coverage"
        for i, result in enumerate(results):
            assert result.filename != 'file_to_skip.py'
            assert result.filename == measured_files[i]
            assert result.lines == lines_data[measured_files[i]]
