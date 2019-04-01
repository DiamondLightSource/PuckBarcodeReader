import unittest

import os
from mock import MagicMock

from dls_barcode.data_store.comms_manager import CommsManager
from dls_barcode.data_store.record import Record

ID0 = "id0"
ID1 = "id1"
ID2 = "id2"
ID3 = "id3"


class TestCommsManager(unittest.TestCase):

    def setUp(self):
        self.directory = MagicMock()
        self.directory.value.return_value = 'dir'
        self.file_name = 'test'

    def test_load_records_from_file_returns_empty_record_list_when_no_file(self):
        cm = CommsManager(self.directory, self.file_name)
        records = cm.load_records_from_file()

        self.assertEqual(len(records), 0)

    def test_load_record_skip_invalid_lines(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.read_lines.return_value = self._invalid_record_strings()

        # Act
        records = cm.load_records_from_file()

        # Assert
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].id, ID0)
        self.assertEqual(records[1].id, ID2)

    def test_to_file_stores_records_in_file(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory.value.return_value, self.file_name + ".txt")
        records = self._get_records()

        # Act
        cm.to_file(records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertIn(file_name, filename_used)
        for r, l in zip(records, record_lines_used):
            self.assertIn(r.to_string(), l)

    def test_to_file_csv_store_in_csv_file(self):
        # Arrange
        cm = CommsManager(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory.value.return_value, self.file_name + ".csv")
        records = self._get_records()

        # Act
        cm.to_csv_file(records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertEqual(file_name, filename_used)
        for r, l in zip(records, record_lines_used):
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


    def _invalid_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238925.0;test.png;None;DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";Invalid record string")
        str_rep.append(ID2 + ";1494238921.0;test.png;None;DLSL-008,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

    def _get_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238923.0;test" + ID0 + ".png;None;DLSL-001,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";1494238922.0;test" + ID1 + ".png;None;DLSL-002,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID2 + ";1494238921.0;test" + ID2 + ".png;None;DLSL-003,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID3 + ";1494238920.0;test" + ID3 + ".png;None;DLSL-004,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

    def _get_records(self):
        strings = self._get_record_strings()
        rep = list()
        for str in strings:
            rep.append(Record.from_string(str))
        return rep




