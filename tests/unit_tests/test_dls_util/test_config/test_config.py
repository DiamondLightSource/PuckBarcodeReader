import unittest
import os

from dls_util import Config, IntConfigItem


class TestConfig(unittest.TestCase):

    def test_init_creates_empty_item_table(self):
        cof = Config('test_config.ini')
        items = cof._items
        self.assertEquals(len(items), 0)

    def test_add_adds_an_item_of_given_class_tag_and_default_to_list_of_items(self):
        conf = Config('test_config.ini')
        conf.add(IntConfigItem, "Camera Number", -1);
        item = conf._items[0]
        self.assertEquals(item.tag(), "Camera Number")
        self.assertTrue(isinstance(item, IntConfigItem))
        self.assertEqual(item._default, -1)
        self.assertEquals(item.value(), None)

    def test_add_adds_an_item_of_given_class_tag_default_and_extra_to_list_of_items_(self):
        conf = Config('test_config.ini')
        conf.add(IntConfigItem, "Camera Number", -1, "m");
        item = conf._items[0]
        self.assertEquals(item.tag(), "Camera Number")
        self.assertTrue(isinstance(item, IntConfigItem))
        self.assertEqual(item._default, -1)
        self.assertEqual(item.units(), "m")
        self.assertEquals(item.value(), None)

    def test_reset_all_sets_value_of_all_items_to_default(self):
        conf = Config('test_config.ini')
        conf.add(IntConfigItem, "Camera Number", -1, "m");
        conf.add(IntConfigItem, "Puck Camera Width", 100, "m")
        conf.add(IntConfigItem, "Puck Camera Height", 50, "m")
        camera_number_item = conf._items[0]
        camera_w_item = conf._items[1]
        camera_h_item = conf._items[2]

        camera_number_item.set(155)
        camera_w_item.set(15)
        camera_h_item.set(3)

        self.assertEquals(camera_number_item.value(), 155)
        self.assertEquals(camera_w_item.value(), 15)
        self.assertEquals(camera_h_item.value(), 3)
        conf.reset_all()

        self.assertEquals(camera_number_item.value(), -1)
        self.assertEquals(camera_w_item.value(), 100)
        self.assertEquals(camera_h_item.value(), 50)

    def test_save_to_file_saves_values_to_file_from_constructor(self):
        file = 'test_config_new.ini'
        conf = Config(file)
        conf.add(IntConfigItem, "Camera Number", -1, "m");
        conf.add(IntConfigItem, "Puck Camera Width", 100, "m")
        conf.add(IntConfigItem, "Puck Camera Height", 50, "m")
        camera_number_item = conf._items[0]
        camera_w_item = conf._items[1]
        camera_h_item = conf._items[2]
        camera_number_item.set(155)
        camera_w_item.set(15)
        camera_h_item.set(3)
        conf.save_to_file()
        with open(file) as f:
            lines = f.readlines()
        self.assertTrue("Camera Number=155" in lines[0])
        self.assertTrue("Puck Camera Width=15" in lines[1])
        self.assertTrue("Puck Camera Height=3" in lines[2])
        os.remove(file)

    #TODO : load saves mixed - need to refactor it at some point
    def test_initialise_from_file_creates_new_file_if_the_given_does_not_exist(self):
        file = 'new_file.ini'
        conf = Config(file)
        conf.add(IntConfigItem, "Camera Number", -1, "m");
        conf.add(IntConfigItem, "Puck Camera Width", 100, "m")
        conf.add(IntConfigItem, "Puck Camera Height", 50, "m")
        camera_number_item = conf._items[0]
        camera_w_item = conf._items[1]
        camera_h_item = conf._items[2]
        camera_number_item.set(155)
        camera_w_item.set(15)
        camera_h_item.set(3)
        self.assertFalse(os.path.isfile(file))
        conf.initialize_from_file()
        self.assertTrue(os.path.isfile(file))
        os.remove(file)

# TODO: fix the following tests so they can run regardless of where the tests are launched from
    # def test_initialise_from_file_sets_default_if_patter_broken_in_the_file(self):
    #     conf = Config('test_config.ini')
    #     conf.add(IntConfigItem, "Side Camera Number", 33)
    #     item = conf._items[0]
    #     conf.initialize_from_file()
    #     self.assertEquals(item.value(), 33)

    # def test_initialise_from_file_sets_default_if_tags_dont_match(self):
    #     conf = Config('test_config.ini')
    #     conf.add(IntConfigItem, "BadTag", 500)
    #     item = conf._items[0]
    #     conf.initialize_from_file()
    #     self.assertEquals(item.value(), 500)
    #
    #
    # def test_initialize_from_file_sets_value_from_file_if_tags_match(self):
    #     conf = Config('test_config.ini')
    #     conf.add(IntConfigItem, "Camera Number", -1)
    #     conf.initialize_from_file()
    #     self.assertEquals(len(conf._items), 1)
    #     item = conf._items[0]
    #     self.assertEquals(item.value(), 10)
    #
    #
    #

