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

#> replaced with >= in the return statement
    def test_paste_when_location_is_outside_image_negative_coordinates_same_as_size_of_src_image_3_channels(self):
        image_target = Image.blank(10, 10)
        image_src = Image(img=np.full((2, 2, 3), 2, np.uint8))
        image_target.paste(image_src, -2, 0)
        a = np.sum(image_target.img)
        self.assertEquals(a, 0)

    def test_paste_when_location_is_outside_image_negative_coordinates_3_channels(self):
        image_target = Image.blank(10, 10)
        image_src = Image(img=np.full((2, 2, 3), 2, np.uint8))
        image_target.paste(image_src, -10, 0)
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

    def test_paste_when_location_is_inside_image_4_channels_no_blending_when_source_alpha_is_255(self):
        image_target = Image(img=np.full((10, 10, 4), 30.0, np.uint8))
        image_src = Image(img=np.full((1, 1, 4), 255.0, np.uint8))
        a = np.sum(image_src.img[0:1, 0:1, 0:3])
        image_target.paste(image_src, 0, 0)
        b = np.sum(image_target.img[0:1, 0:1, 0:3])
        self.assertEquals(a, b) #target changed into source


    def test_paste_when_location_is_inside_image_4_channels_blending_works(self):
        image_target = Image(img=np.full((10, 10, 4), 10, np.uint8))
        image_src = Image(img=np.full((1, 1, 4), 25, np.uint8))
        image_target.paste(image_src, 0, 0)
        a = np.sum(image_src.img[0:1, 0:1, 0:3])
        b = np.sum(image_target.img[0:1, 0:1, 0:3])
        self.assertNotEquals(a, b)
        self.assertEquals(b, 33)


    #this is rather surprising??
    def test_paste_when_location_is_inside_image_4_target_alpha_does_not_matter(self):
        image_target = Image(img=np.full((10, 10, 4), 10, np.uint8))
        image_src = Image(img=np.full((1, 1, 4), 25, np.uint8))
        image_target.paste(image_src, 0, 0)
        b = np.sum(image_target.img[0:1, 0:1, 0:3])
        self.assertEquals(b, 33)

        array = np.full((10, 10, 4), 10, np.uint8)
        array[:, :, 3] = np.ones((10, 10), np.uint8)
        image_target_new = Image(img=array)
        image_src_new = Image(img=np.full((1, 1, 4), 25, np.uint8))
        image_target_new.paste(image_src_new, 0, 0)
        c = np.sum(image_target_new.img[0:1, 0:1, 0:3])
        self.assertEquals(c, 33)
        self.assertEquals(b, c)

    #why???
    def target_image_alpha_becomes_255_after_paste(self):
        image_target = Image(img=np.full((5, 5, 4), 10, np.uint8))
        max_alpha_before_paste = np.max(image_target.img[:, :, 3])
        image_src = Image(img=np.full((1, 1, 4), 25, np.uint8))
        image_target.paste(image_src, 0, 0)
        max_alpha_after_paste = np.max(image_target.img[:, :, 3])

        self.assertEquals(max_alpha_before_paste, 10)
        self.assertEquals(max_alpha_after_paste, 255) #I expected it to be as it was before


    #def test_sub_image

    #def test_calculate_brightness