import unittest
import cv2

from dls_util.image import Image, Color
from dls_util.shape import Point, Circle
from dls_util.cv.circle_detector  import CircleDetector

class TestCircleDetector(unittest.TestCase):

    def test_init_sets_canny_thresh(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._canny_thresh, 150)

    def test_init_sets_accumulator_thresh(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._accumulator_thresh, 100)

    def test_init_sets_dp(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._dp, 2)

    def test_init_sets_min_dist(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._min_dist, 100)

    def test_init_sets_min_radius(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._min_radius, 100)

    def test_init_sets_max_radius(self):
        decorator = CircleDetector()
        self.assertEqual(decorator._max_radius, 150)

    def test_set_canny_thresh_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_canny_threshold(400)
        self.assertEqual(decorator._canny_thresh, 400)

    def test_set_accumulator_threshold_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_accumulator_threshold(0)
        self.assertEqual(decorator._accumulator_thresh, 0)

    def test_set_dp_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_dp(3)
        self.assertEqual(decorator._dp, 3)

    def test_set_minimum_separation_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_minimum_separation(300)
        self.assertEqual(decorator._min_dist, 300)

    def test_set_minimum_radius_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_minimum_radius(50)
        self.assertEqual(decorator._min_radius, 50)

    def test_set_maximum_radius_sets_the_value_correctly(self):
        decorator = CircleDetector()
        decorator.set_maximum_radius(30)
        self.assertEqual(decorator._max_radius, 30)

    def test_no_circle_detected_in_blan_image(self):
        img = Image.blank(100,100,1,0)
        decorator = CircleDetector()
        list_of_circle = decorator.find_circles(img);
        self.assertEqual(list_of_circle.__len__(),0)

    def test_circle_is_correctly_detected_when_there_is_one_circle_in_the_image(self):
        img = Image.blank(40, 40)
        circle = Circle(Point(20, 20), 10)
        img.draw_circle(circle, Color(200, 200, 200),2)
        grey = img.to_grayscale()
        #parameters of the detector very important - a bit dubious test
        decorator = CircleDetector()
        decorator.set_maximum_radius(20)
        decorator.set_minimum_radius(5)
        decorator.set_accumulator_threshold(20)
        decorator.set_canny_threshold(20)

        list = decorator.find_circles(grey)

        self.assertEqual(list.__len__(), 1)
       # self.assertEqual(list[0].radius(), circle.radius())
        #self.assertEqual(list[0].center().x, circle.center().x + 1)
        #self.assertEqual(list[0].center().y, circle.center().y + 1)
        self.assertEqual(list[0].area(), circle.area())


    def test_circle_is_correctly_detected_when_there_there_are_two_circles_in_the_image_not_intersecting(self):

        img = Image.blank(100, 100)
        circle_a = Circle(Point(20, 20), 10)
        circle_b = Circle(Point(50, 50), 10)
        img.draw_circle(circle_a, Color(10, 50, 100), 2)
        img.draw_circle(circle_b, Color(10, 50, 100), 2)
        grey = img.to_grayscale()

        decorator = CircleDetector()
        decorator.set_maximum_radius(20)
        decorator.set_minimum_radius(5)
        decorator.set_accumulator_threshold(30)
        decorator.set_canny_threshold(30)
        decorator.set_minimum_separation(10)

        list = decorator.find_circles(grey)

        self.assertEqual(list.__len__(), 2)

    #def test_circle_is_correctly_detected_when_there_there_are_two_circles_and_rectangle_not_intersecting(self):








