import shutil
import unittest

import os
from mock import MagicMock

from dls_barcode.data_store.store_writer import StoreWriter


class TestStoreWriter(unittest.TestCase):

    def setUp(self):
        self.directory = MagicMock()

        self.directory = 'dir'
        self.file_name = 'test'
        record_one = MagicMock()
        record_one.to_csv_string.return_value = 'csv_string_one'
        record_one.to_string.return_value = 'string_one'
        record_two = MagicMock()
        record_two.to_csv_string.return_value = 'csv_string_two'
        record_two.to_string.return_value = 'string_two'
        record_three = MagicMock()
        record_three.to_csv_string.return_value = 'csv_string_three'
        record_three.to_string.return_value = 'string_three'
        self.records = [record_one, record_two, record_three]

    def test_to_file_stores_records_in_file(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory, self.file_name + ".txt")

        # Act
        cm.to_file(self.records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertIn(file_name, filename_used)
        for r, l in zip(self.records, record_lines_used):
            self.assertIn(r.to_string(), l)

    def test_to_file_csv_store_in_csv_file(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        file_name = os.path.join(self.directory, self.file_name + ".csv")

        # Act
        cm.to_csv_file(self.records)

        # Assert
        ((filename_used, record_lines_used), kwargs) = cm._file_manager.write_lines.call_args_list[0]
        self.assertEqual(file_name, filename_used)
        for r, l in zip(self.records, record_lines_used):
            self.assertIn(r.to_csv_string(), l)

    def test_make_image_dir_attempts_to_create_img_dir(self):

        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        img_dir = os.path.join(self.directory, "img_dir")

        # Act
        cm._make_img_dir()

        # Assert
        self.assertEqual(cm._file_manager.make_dir_when_no_dir.call_count, 2)
        cm._file_manager.make_dir_when_no_dir.assert_called_with(img_dir)

    def test_remove_image_file_attempts_to_remove_file_when_it_exists(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_file.return_value = True

        # Act
        cm.remove_img_file(MagicMock())

        # Assert
        self.assertEqual(cm._file_manager.remove.call_count, 2)
                 
    def test_remove_image_file_does_not_attempt_to_remove_file_when_it_does_not_exists(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._file_manager = MagicMock()
        cm._file_manager.is_file.return_value = False

        # Act
        cm.remove_img_file(MagicMock())

        # Assert
        cm._file_manager.remove.assert_not_called()

    def test_to_image_calls_image_save_as(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        pin_image = MagicMock()
        holder_image = MagicMock()
        
        # Act
        cm.to_image(pin_image, holder_image, 'test_image')
         
         # Assert
        pin_image.save_as.assert_called_once()

    def test_to_image_sets_image_path(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        
        # Act
        self.assertIsNone((cm.get_img_path()))
        cm.to_image(MagicMock(), MagicMock(), 'name')
        
        # Assert
        self.assertIsNotNone((cm.get_img_path()))

    def test_to_image_makes_img_dir(self):
         # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm._make_img_dir = MagicMock()
        cm._make_img_dir.return_value = 'dir'
        
        # Act
        cm.to_image(MagicMock(), MagicMock(), 'name')
        
        # Assert
        cm._make_img_dir.assert_called_once()

    def test_get_img_path_returns_none_if_to_image_not_called(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm.to_image = MagicMock()
        
        # Act
        cm.to_image.assert_not_called()
        
        # Assert
        self.assertIsNone(cm.get_img_path())

    def test_get_image_returns_image_path(self):
        # Arrange
        cm = StoreWriter(self.directory, self.file_name)
        cm.to_image(MagicMock(), MagicMock(), 'test_image')
        
        # Act
        path = cm.get_img_path()
        
        # Assert
        self.assertIsNotNone(path)
        self.assertIn('test_image', path)
        self.assertIn("img_dir", path)
        self.assertIn(self.directory, path)

    @classmethod
    def tearDownClass(cls):
        if os.path.isdir('dir'):
            shutil.rmtree('dir')
