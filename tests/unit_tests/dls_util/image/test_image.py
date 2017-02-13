import unittest
import numpy as np

from dls_util.image import Image


class TestImage(unittest.TestCase):

    def test_paste_when_location_is_outside_image_x_off(self):
        image_target = Image.blank(10, 10)
        image_src = Image(img=np.full((5, 5, 3), 2, np.uint8))
        image_target.paste(image_src, 20, 0)
        a = np.sum(image_target.img)
        self.assertEquals(a, 0)

    def test_paste_when_location_is_outside_image_y_off(self):
        image_target = Image.blank(10, 10)
        image_src = Image(img=np.full((5, 5, 3), 2, np.uint8))
        image_target.paste(image_src, 0, 20)
        a = np.sum(image_target.img)
        self.assertEquals(a, 0)

    def test_paste_when_location_is_inside_image_3_channels(self):
        image_target = Image.blank(10, 10)
        image_src = Image(img=np.full((1, 1, 3), 2, np.uint8))
        image_target.paste(image_src, 0, 0)
        a = np.sum(image_target.img)
        self.assertEquals(a, 6)
        self.assertEquals(image_target.img[0, 0, 1], 2)
        self.assertEquals(image_target.img[0, 1, 1], 0)

    #def test_paste_when_location_is_inside_image_4_channels(self):

    #def test_sub_image

    #def test_calculate_brightness