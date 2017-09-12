import unittest
from dls_util.config import IntConfigItem

class TestIntConfigItem(unittest.TestCase):

    def test_item_is_initialised_correctly_without_units(self):
        # Arrange
        tag = "A tag"
        default_value = 5

        # Act
        item = IntConfigItem(tag, default_value)

        # Assert
        self.assertEqual(item.tag(), tag)
        self.assertIsNone(item.value())

    def test_valid_integer_value_is_set_correctly(self):
        # Arrange
        item = self._create_item()
        valid_value = 15

        # Act
        item.set(valid_value)

        # Assert
        self.assertEqual(item.value(), valid_value)

    def test_reset_sets_the_value_to_default(self):
        # Arrange
        expected_default = 12
        item = self._create_item(default_value=expected_default)
        new_value = 6
        item.set(new_value)

        # Act
        item.reset()

        # Assert
        self.assertEqual(item.value(), expected_default)

    def test_when_setting_double_value_then_value_is_rounded(self):
        # Arrange
        item = self._create_item()
        double_value = 1.9
        expected_value = int(double_value)

        # Act
        item.set(double_value)

        # Assert
        self.assertEqual(item.value(), expected_value)

    def test_value_can_be_set_from_string_of_integer(self):
        # Arrange
        item = self._create_item()
        string_value = "77"
        expected_value = 77

        # Act
        item.from_file_string(string_value)

        # Assert
        self.assertEqual(item.value(), expected_value)

    def test_when_setting_string_that_is_not_an_integer_then_value_is_set_to_default(self):
        # Arrange
        expected_default = 123
        item = self._create_item(default_value=expected_default)
        invalid_string = "456.4"

        # Act
        item.from_file_string(invalid_string)

        # Assert
        self.assertEqual(item.value(), expected_default)

    def _create_item(self, tag = "A tag", default_value = 5):
        return IntConfigItem(tag, default_value)

