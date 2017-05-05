import unittest
from dls_util import ConfigItem, IntConfigItem, DirectoryConfigItem, BoolConfigItem, EnumConfigItem

class TestItem(unittest.TestCase):


    def test_value_returns_None_If_value_not_set(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals(item.value(), None)

    def test_if_set_and_returned_values_are_the_same(self):
        item = ConfigItem("test_int", 2)
        item.set(10)
        self.assertEquals(item.value(), 10)

    def test_tag_returns_correctly(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals( item.tag(), "test_int")

    def test_reset_sets_value_to_default(self):
        item = ConfigItem("test_int", 2)
        item.set(10)
        self.assertEquals(item.value(), 10)
        item.reset()
        self.assertEquals(item.value(), 2)

    def test_to_file_string_create_string_correctly_formatted(self):
        item = ConfigItem("test_int", 2)
        item.set(30)
        str = item.to_file_string()
        self.assertEquals(str, "test_int=30\n")

class TestIntConfigItem(unittest.TestCase):

    def test_units_returns_cam_if_set_to_cm_in_constructor(self):
        item = IntConfigItem("test_int", 2, 'cm')
        self.assertEquals(item.units(), 'cm')

    def test_from_file_string_sets_default_value_if_not_int(self):
        item = IntConfigItem("test_int", 2, 'cm')
        item.from_file_string("buu")
        self.assertEquals(item.value(), 2)

    def test_from_file_string_sets_int_value_correctly(self):
        item = IntConfigItem("test_int", 2, 'cm')
        item.from_file_string("20")
        self.assertEquals(item.value(), 20)

class TestDirectoryConfigItem(unittest.TestCase):

    def test_from_file_string_sets_value_as_string_finished_with_slash(self):
        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("20")
        self.assertEquals(item.value(), "20/")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string(20)
        self.assertEquals(item.value(), "20/")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("test")
        self.assertEquals(item.value(), "test/")

        item = DirectoryConfigItem("test_int", 15)
        item.from_file_string("test/")
        self.assertEquals(item.value(), "test/")

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
        self.assertEquals(item._default, "15")

        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        self.assertEquals(item._default, "test")

    def test_init_sets_def_to_the_first_value_from_possible_enum_names_if_def_not_in_possible_names(self):
        item = EnumConfigItem("test_int", 1, [15,16,17])
        self.assertEquals(item._default, "15")

    def test_from_file_string_sets_stripped_string_value_if_it_is_in_enum_names(self):
        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        item.from_file_string("   test2   ")
        self.assertEquals(item.value(), "test2")

    def test_from_file_string_sets_default_value_if_the_value_is_not_in_enum_names(self):
        item = EnumConfigItem("test_int", "test", ["test", "test1", "test2"])
        item.from_file_string("te")
        self.assertEquals(item.value(), "test")




















