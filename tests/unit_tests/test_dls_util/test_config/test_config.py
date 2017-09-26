import unittest
from mock import MagicMock
import os

from dls_util import Config, IntConfigItem


class TestConfig(unittest.TestCase):

    def setUp(self):
        self._file = "a_file_path.ini"
        self._mock_file_manager = MagicMock()

    def test_new_config_has_no_items(self):
        # Act
        conf = self._create_config()

        # Assert
        items = conf.get_items()
        self.assertEquals(len(items), 0)

    def test_an_item_of_given_class_tag_and_default_value_can_be_added_to_config(self):
        # Arrange
        conf = self._create_config()
        tag = "Camera Number"
        default = -1
        expected_value = None

        # Act
        conf.add(IntConfigItem, tag, default);

        # Assert
        item = conf.get_items()[0]
        self.assertTrue(isinstance(item, IntConfigItem))
        self.assertEquals(item.tag(), tag)
        self.assertEqual(item._default, default)
        self.assertEquals(item.value(), expected_value)

    def test_an_item_of_given_class_tag_default_value_and_extra_arg_can_be_added_to_config(self):
        # Arrange
        conf = self._create_config()
        tag = "Length"
        default = 101
        expected_value = None
        units = "m"

        # Act
        conf.add(IntConfigItem, tag, default, units)

        # Assert
        item = conf.get_items()[0]
        self.assertTrue(isinstance(item, IntConfigItem))
        self.assertEquals(item.tag(), tag)
        self.assertEqual(item._default, default)
        self.assertEqual(item.units(), units)
        self.assertEquals(item.value(), expected_value)

    def test_reset_all_sets_value_of_all_items_to_default(self):
        # Arrange
        conf = self._create_config()
        default_number = 0
        default_width = 100
        new_number = 155
        new_width = 15
        conf.add(IntConfigItem, "Camera Number", default_number);
        conf.add(IntConfigItem, "Puck Camera Width", default_width)

        number_item = conf.get_items()[0]
        width_item = conf.get_items()[1]

        number_item.set(new_number)
        width_item.set(new_width)

        self.assertEquals(number_item.value(), new_number)
        self.assertEquals(width_item.value(), new_width)

        # Act
        conf.reset_all()

        # Assert
        self.assertEquals(number_item.value(), default_number)
        self.assertEquals(width_item.value(), default_width)

    def test_config_can_be_saved_to_file(self):
        # Arrange
        conf = self._create_config()

        conf.add(IntConfigItem, "Camera Number", -1, "m");
        conf.add(IntConfigItem, "Puck Camera Width", 100, "m")
        conf.add(IntConfigItem, "Puck Camera Height", 50, "m")

        camera_number_item = conf.get_items()[0]
        camera_w_item = conf.get_items()[1]
        camera_h_item = conf.get_items()[2]

        camera_number_item.set(155)
        camera_w_item.set(15)
        camera_h_item.set(3)

        expected_lines = []
        expected_lines.append(camera_number_item.to_file_string())
        expected_lines.append(camera_w_item.to_file_string())
        expected_lines.append(camera_h_item.to_file_string())

        # Act
        conf.save_to_file()

        # Assert
        self._mock_file_manager.write_lines.assert_called_once_with(self._file, expected_lines)

    def test_initialise_from_file_creates_new_file_using_default_values_if_the_given_file_does_not_exist(self):
        # Arrange
        self._mock_file_manager.exists.return_value = False
        conf = self._create_config()
        default_value = 234
        conf.add(IntConfigItem, "Camera Number", default_value, "m");

        camera_number_item = conf.get_items()[0]
        self.assertIsNone(camera_number_item.value())

        # Act
        conf.initialize_from_file()

        # Assert
        self.assertEqual(camera_number_item.value(), default_value)
        expected_file_content = [camera_number_item.to_file_string()]
        self._mock_file_manager.write_lines.assert_called_once_with(self._file, expected_file_content)

    def test_initialise_from_file_does_not_write_to_file_if_the_given_file_exists(self):
        # Arrange
        self._mock_file_manager.exists.return_value = True
        conf = self._create_config()
        conf.add(IntConfigItem, "Camera Number", 22, "m");

        # Act
        conf.initialize_from_file()

        # Assert
        self._mock_file_manager.write_lines.assert_not_called()

    def test_initialise_from_file_sets_default_if_pattern_broken_in_the_file(self):
        # Arrange
        self._mock_file_manager.exists.return_value = True
        self._mock_file_manager.read_lines.return_value = ["Side Camera Number===1\n"]
        conf = self._create_config()
        default = 33
        conf.add(IntConfigItem, "Side Camera Number", default)

        item = conf.get_items()[0]
        self.assertIsNone(item.value())

        # Act
        conf.initialize_from_file()

        # Assert
        self.assertEquals(item.value(), default)

    def test_initialise_from_file_sets_default_if_tags_dont_match(self):
        # Arrange
        self._mock_file_manager.exists.return_value = True
        self._mock_file_manager.read_lines.return_value = ["BadTagg=60\n"]
        conf = self._create_config()
        default = 500
        conf.add(IntConfigItem, "BadTag", default)

        item = conf.get_items()[0]
        self.assertIsNone(item.value())

        # Act
        conf.initialize_from_file()

        # Assert
        self.assertEquals(item.value(), default)

    def test_initialize_from_file_sets_value_from_file_if_tags_match(self):
        # Arrange
        expected_value = 10
        self._mock_file_manager.exists.return_value = True
        self._mock_file_manager.read_lines.return_value = ["Camera Number=" + str(expected_value) + "\n"]
        conf = self._create_config()
        conf.add(IntConfigItem, "Camera Number", -1)

        # Act
        conf.initialize_from_file()

        # Assert
        item = conf.get_items()[0]
        self.assertEquals(item.value(), expected_value)

    def _create_config(self):
        return Config(self._file, self._mock_file_manager)




