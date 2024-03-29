import unittest
from dls_util.config import ConfigItem, IntConfigItem, DirectoryConfigItem, BoolConfigItem, EnumConfigItem

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

    def test_units_are_initialised_correctly(self):
        # Arrange
        tag = "A tag"
        default_value = 5
        units = "ms"

        # Act
        item = IntConfigItem(tag, default_value, units)

        # Assert
        self.assertEqual(item.units(), units)

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


class TestConfigItem(unittest.TestCase):

    def test_value_returns_None_If_value_not_set(self):
        item = ConfigItem("test_int", 2)
        self.assertEqual(item.value(), None)

    def test_if_set_and_returned_values_are_the_same(self):
        item = ConfigItem("test_int", 2)
        item.set(10)
        self.assertEqual(item.value(), 10)

    def test_tag_returns_correctly(self):
        item = ConfigItem("test_int", 2)
        self.assertEqual( item.tag(), "test_int")

    def test_reset_sets_value_to_default(self):
        item = ConfigItem("test_int", 2)
        item.set(10)
        self.assertEqual(item.value(), 10)
        item.reset()
        self.assertEqual(item.value(), 2)

    def test_to_file_string_create_string_correctly_formatted(self):
        item = ConfigItem("test_int", 2)
        item.set(30)
        str = item.to_file_string()
        self.assertEqual(str, "test_int=30\n")

class TestDirectoryConfigItem(unittest.TestCase):

    def test_from_file_string_sets_value_as_stripped_string(self):
        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("  20 ")
        self.assertEqual(item.value(), "20")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string(20)
        self.assertEqual(item.value(), "20")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("test")
        self.assertEqual(item.value(), "test")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("test/  ")
        self.assertEqual(item.value(), "test/")

class TestBoolConfigItem(unittest.TestCase):

    def test_from_file_string_sets_value_True_when_input_string_is_true(self):
        item = BoolConfigItem("test_int", 15)
        item.from_file_string("TrUE")
        self.assertTrue(item.value())

        item.from_file_string("trUE")
        self.assertTrue(item.value())

    def test_from_file_string_sets_value_Fale_when_input_string_is_other_than_True(self):
        item = BoolConfigItem("test_int", 15)
        item.from_file_string("AAAAA")
        self.assertFalse(item.value())


class TestEnumConfigItem(unittest.TestCase):

    def test_init_sets_def_value_if_it_is_one_of_possible_enum_names(self):
        item = EnumConfigItem("test_int", 15, [15,16,17])
        self.assertEqual(item._default, "15")

        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        self.assertEqual(item._default, "test")

    def test_init_sets_def_to_the_first_value_from_possible_enum_names_if_def_not_in_possible_names(self):
        item = EnumConfigItem("test_int", 1, [15,16,17])
        self.assertEqual(item._default, "15")

    def test_from_file_string_sets_stripped_string_value_if_it_is_in_enum_names(self):
        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        item.from_file_string("   test2   ")
        self.assertEqual(item.value(), "test2")

    def test_from_file_string_sets_default_value_if_the_value_is_not_in_enum_names(self):
        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        item.from_file_string("te")
        self.assertEqual(item.value(), "test")




















