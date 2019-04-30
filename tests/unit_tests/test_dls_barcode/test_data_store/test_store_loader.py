import unittest

from mock import MagicMock

from dls_barcode.data_store.store_loader import StoreLoader


class TestStoreLoader(unittest.TestCase):

    def setUp(self):
        self.directory = MagicMock()

        self.directory = 'dir'
        self.file_name = 'test'

    def test_load_records_from_file_returns_empty_record_list_when_no_file(self):
        cm = StoreLoader(self.directory, self.file_name)
        records = cm.load_records_from_file()

        self.assertEqual(len(records), 0)

    def test_load_record_skip_invalid_lines(self):
        # Arrange
        cm = StoreLoader(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.read_lines.return_value = [MagicMock(), MagicMock()]

        # Act
        records = cm.load_records_from_file()

        # Assert
        self.assertEqual(len(records), 0)

