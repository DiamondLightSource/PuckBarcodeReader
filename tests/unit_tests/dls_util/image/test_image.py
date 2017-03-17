import unittest
import numpy as np

from dls_util.image import Image, Color
from dls_util.shape import Point, Circle



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

    def test_draw_circle_thickness_equals_one(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 10)
        img.draw_circle(circle, Color(200, 200, 200), 1)
        self.assertEquals(img.img[10][20][1], 200)
        self.assertEquals(img.img[9][20][1], 0)
        self.assertEquals(img.img[11][20][1], 0)

    def test_draw_circle_thickness_equals_two(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 10)
        img.draw_circle(circle, Color(200, 200, 200), 2)
        self.assertEquals(img.img[8][20][1], 0)
        self.assertEquals(img.img[10][20][1], 200)
        self.assertEquals(img.img[9][20][1], 200)
        self.assertEquals(img.img[11][20][1], 200)
        self.assertEquals(img.img[12][20][1], 0)

    def test_draw_circle_thickness_equals_three(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 10)
        img.draw_circle(circle, Color(200, 200, 200), 3)
        self.assertEquals(img.img[7][20][1], 0)
        self.assertEquals(img.img[8][20][1], 200)
        self.assertEquals(img.img[10][20][1], 200)
        self.assertEquals(img.img[9][20][1], 200)
        self.assertEquals(img.img[11][20][1], 200)
        self.assertEquals(img.img[12][20][1], 200)
        self.assertEquals(img.img[13][20][1], 0)

    #very confusing thickness 3 and 4 give the same results
    def test_draw_circle_thickness_equals_four(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 10)
        img.draw_circle(circle, Color(200, 200, 200), 4)
        self.assertEquals(img.img[6][20][1], 0)
        self.assertEquals(img.img[7][20][1], 0)#!!
        self.assertEquals(img.img[8][20][1], 200)
        self.assertEquals(img.img[10][20][1], 200)
        self.assertEquals(img.img[9][20][1], 200)
        self.assertEquals(img.img[11][20][1], 200)
        self.assertEquals(img.img[12][20][1], 200)
        self.assertEquals(img.img[13][20][1], 0)#!!
        self.assertEquals(img.img[14][20][1], 0)


    def test_draw_circle_centre_is_kept(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 1)
        img.draw_circle(circle, Color(200, 200, 200), 1)
        self.assertEquals(img.img[18][20][1], 0)
        self.assertEquals(img.img[19][20][1], 200)
        self.assertEquals(img.img[20][20][1], 0)
        self.assertEquals(img.img[21][20][1], 200)
        self.assertEquals(img.img[22][20][1], 0)

        self.assertEquals(img.img[20][18][1], 0)
        self.assertEquals(img.img[20][19][1], 200)
        self.assertEquals(img.img[20][20][1], 0)
        self.assertEquals(img.img[20][21][1], 200)
        self.assertEquals(img.img[20][22][1], 0)



    #def test_sub_image
    def test_sub_image_is_square_with_side_length_2_radius_if_enough_space_to_cut_from(self):
        image = Image.blank(10,10,3,0)

        x_center = 5
        y_center = 5
        radius = 2
        sub_image, roi = image.sub_image(Point(x_center,y_center),radius) #sub_image returns a raw cv image

        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, 2*radius)
        self.assertEquals(height, 2*radius)
        self.assertEquals(width, height)

    def test_sub_image_is_not_square_if_center_x_is_too_close_to_the_edge(self):
        image = Image.blank(10, 10, 3, 0)
        x_center = 9
        y_center = 5
        radius = 2
        sub_image, roi = image.sub_image(Point(x_center, y_center), radius)
        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, 3)
        self.assertEquals(height, 2*radius)
        self.assertNotEquals(width, height)

    def test_sub_image_is_not_square_if_center_x_is_too_close_to_the_edge(self):
        image = Image.blank(10, 10, 3, 0)

        x_center = 5
        y_center = 1
        radius = 2
        sub_image, roi = image.sub_image(Point(x_center, y_center), radius)

        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, 2*radius)
        self.assertEquals(height, 3)
        self.assertNotEquals(width, height)

    def test_sub_image_has_size_of_input_image_if_2xradius_covers_the_whole_image(self):
        image = Image.blank(5, 6, 3, 0)
        x_center = 2
        y_center = 2
        radius = 7
        sub_image, roi = image.sub_image(Point(x_center, y_center), radius)
        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, image.width)
        self.assertEquals(height, image.height)

    def test_sub_image_has_size_0x0_if_center_and_radius_outside_the_input_image(self):
        image = Image.blank(5, 6, 3, 0)
        x_center = 10
        y_center = 10
        radius = 2
        sub_image, roi = image.sub_image(Point(x_center, y_center), radius)
        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, 0)
        self.assertEquals(height, 0)


    def test_sub_image_is_created_if_the_center_is_outside_but_the_radius_ovelaps_with_input_image(self):
        image = Image.blank(9, 9, 3, 0)
        x_center = 10
        y_center = 10
        radius = 2
        sub_image, roi = image.sub_image(Point(x_center, y_center), radius)
        height = sub_image.height
        width = sub_image.width
        self.assertEquals(width, 1)
        self.assertEquals(height, 1)

    #def test_calculate_brightness