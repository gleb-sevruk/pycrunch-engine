import unittest
from unittest import mock
from unittest.mock import Mock, mock_open

from pycrunch.session.auto_configuration import AutoConfiguration


class TestAutoConfigDecision(unittest.TestCase):
    def setUp(self):
        self.config_file_mock = Mock()
        self.create_function_mock = Mock()

    def test_if_config_exists_do_not_create_new(self):
        self.when_configuration_file_already_on_disk()
        sut = self.create_sut()

        sut.ensure_configuration_exist()

        self.create_function_mock.assert_not_called()

    def test_if_no_config_should_call_create_default(self):
        self.when_file_does_not_exist()
        sut = self.create_sut()

        sut.ensure_configuration_exist()

        self.create_function_mock.assert_called_once()

    def create_sut(self):
        sut = AutoConfiguration(self.config_file_mock)
        sut.create_default_configuration_file = self.create_function_mock
        return sut

    def when_file_does_not_exist(self):
        self.set_config_file_existence(False)

    def when_configuration_file_already_on_disk(self):
        self.set_config_file_existence(True)

    def set_config_file_existence(self, val):
        self.config_file_mock.exists.return_value = val


class TestAutoConfigCreation(unittest.TestCase):
    def setUp(self):
        self.config_file_mock = Mock()
        self.create_function_mock = Mock()

    def test_writes_to_file_at_path(self):
        mocked_open = mock_open()
        with mock.patch('io.open', mocked_open) as io_mock:
            sut = AutoConfiguration(self.config_file_mock)
            sut.create_default_configuration_file()
            handle = io_mock()
            default_config_file = '''# documentation https://pycrunch.com/docs/configuration-file
engine:
    runtime: pytest'''
            handle.write.assert_called_once_with(default_config_file)

