import unittest
from dls_util import ConfigItem, IntConfigItem

class TestItem(unittest.TestCase):

    def test_init_creates_empty_vale(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals(item._value, None)

    def test_init_tag_is_correct(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals(item._tag, "test_int")

    def test_init_default_is_correct(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals(item._default, 2)

    def test_value_returns_correctly(self):
        item = ConfigItem("test_int", 2)
        self.assertEquals(item.value(), None)

    def test_set_sets_correct_value(self):
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

    def test_units_set_correctly_by_ini(self):
        item = IntConfigItem("test_int", 2, 'mm')
        self.assertEquals(item._units, 'mm')

    def test_unit_returns_correct_value(self):
        item = IntConfigItem("test_int", 2, 'cm')
        self.assertEquals(item.units(), 'cm')

    def test_clean_returns_default_value_if_not_int(self):
        item = IntConfigItem("test_int", 2, 'cm')
        self.assertEquals(item._clean("buu"), 2)

    def test_clean_returns_int_value_correctly(self):
        item = IntConfigItem("test_int", 2, 'cm')
        self.assertEquals(item._clean("20"), 20)
















