import unittest
import cv2

from dls_util.image import Image


class TestImage(unittest.TestCase):

    def test_is_valid_returns_correct_value(self):
        image = Image(cv2.imread('puck_test.png'))
        self.assertNotEqual(image.width, 0)
        self.assertNotEqual(image.height, 0)
        self.assertTrue(image.is_valid())

    #def test_paste

    #def test_sub_image

    #def test_calculate_brightness