import unittest

import os
from mock import MagicMock

from dls_barcode.data_store.comms_manager import CommsManager

class TestCommsManager(unittest.TestCase):

    def setUp(self):
        self.directory = MagicMock()
        self.directory.value.return_value = 'dir'
        self.file_name = 'test'
        record_one = MagicMock()
        record_one.to_csv_string.return_value  = 'csv_string_one'
        record_one.to_string.return_value = 'string_one'
        record_two = MagicMock()
        record_two.to_csv_string.return_value = 'csv_string_two'
        record_two.to_string.return_value = 'string_two'
        record_three = MagicMock()
        record_three.to_csv_string.return_value = 'csv_string_three'
        record_three.to_string.return_value = 'string_three'
        self.records = [record_one, record_two,record_three]

    def test_load_records_from_file_returns_empty_record_list_when_no_file(self):
        cm = CommsManager(self.directory, self.file_name)
        records = cm.load_records_from_file()

        self.assertEqual(len(records), 0)

    def test_load_record_skip_invalid_lines(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.read_lines.return_value = [MagicMock(), MagicMock()]

        # Act
        records = cm.load_records_from_file()

        # Assert
        self.assertEqual(len(records), 0)

    def test_to_file_stores_records_in_file(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory.value.return_value, self.file_name + ".txt")

        # Act
        cm.to_file(self.records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertIn(file_name, filename_used)
        for r, l in zip(self.records, record_lines_used):
            self.assertIn(r.to_string(), l)

    def test_to_file_csv_store_in_csv_file(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory.value.return_value, self.file_name + ".csv")

        # Act
        cm.to_csv_file(self.records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertEqual(file_name, filename_used)
        for r, l in zip(self.records, record_lines_used):
            self.assertIn(r.to_csv_string(), l)

    def test_make_image_dir_attempts_to_make_dir_if_it_does_not_exist(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_dir.return_value = False
        img_dir = os.path.join(self.directory.value.return_value, "img_dir")

        # Act
        cm.make_img_dir()

        # Assert
        cm._file_manager.is_dir.assert_called_once_with(img_dir)
        cm._file_manager.make_dir.assert_called_once_with(img_dir)

    def test_make_image_dir_doent_make_dir_if_it_does_not_exist(self):

        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_dir.return_value = True
        img_dir = os.path.join(self.directory.value.return_value, "img_dir")

        # Act
        cm.make_img_dir()

        # Assert
        cm._file_manager.is_dir.assert_called_once_with(img_dir)
        cm._file_manager.make_dir.assert_not_called()

    def test_remove_image_file_attempts_to_remove_file_when_it_exists(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_file.return_value = True

        # Act
        cm.remove_img_file(MagicMock())

        # Assert
        cm._file_manager.remove.assert_called_once()

    def test_remove_image_file_does_not_attempt_to_remove_file_when_it_exists(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_file.return_value = False

        # Act
        cm.remove_img_file(MagicMock())

        # Assert
        cm._file_manager.remove.assert_not_called()






