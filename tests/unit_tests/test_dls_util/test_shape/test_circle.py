import unittest

import math

from dls_util.shape import Point

from dls_util.shape import Circle


class TestCircle(unittest.TestCase):

    def test_string_representation_of_circle(self):
        new_circle = Circle(Point(0, 0), 10)
        self.assertEqual(new_circle.__str__(), "Circle - center = (0.00, 0.00); radius = 10.00")

    def test_center_returns_correct_point(self):
        new_circle = Circle(Point(1, 2), 3)
        self.assertEqual(new_circle.center().x, 1)
        self.assertEqual(new_circle.center().y, 2)

    def test_x_y_radius_return_correct_values(self):
        new_circle = Circle(Point(4, 5), 10)
        self.assertEqual(new_circle.x(), 4)
        self.assertEqual(new_circle.y(), 5)
        self.assertEqual(new_circle.radius(), 10)

    def test_diameter_twice_radius(self):
        new_circle = Circle(Point(0, 0), 4)
        self.assertEqual(new_circle.diameter(), 8)

    def test_circumference_is_2pi_r(self):
        new_circle = Circle(Point(4, 0), 4)
        self.assertEqual(new_circle.circumference(), math.pi * 8)

    def test_area_is_2pi_r2(self):
        new_circle = Circle(Point(9, 0), 10)
        self.assertEqual(new_circle.area(), math.pi * 100)

    def test_offset_returns_new_circe_of_same_radius_but_shifted_center(self):
        circle = Circle(Point(3, 0), 10)
        new_circle = circle.offset(Point(3, 3))
        self.assertEqual(new_circle.x(), 6)
        self.assertEqual(new_circle.y(), 3)
        self.assertEqual(new_circle.radius(), 10)

    def test_scale_returns_new_circle_which_is_a_scaled_version_of_input_one(self):
        circle = Circle(Point(3, 0), 10)
        new_circle = circle.offset(Point(3, 3))
        self.assertEqual(new_circle.x(), 6)
        self.assertEqual(new_circle.y(), 3)
        self.assertEqual(new_circle.radius(), 10)

    def test_contains_point_returns_true_if_the_specified_point_is_within_radius(self):
        circle = Circle(Point(0, 0), 10)
        point_center = Point(0, 0)
        self.assertTrue(circle.contains_point(point_center))
        point_middle = Point(5, 5)
        self.assertTrue(circle.contains_point(point_middle))

    def test_contains_point_returns_false_if_the_specified_point_is_on_the_edge(self):
        circle = Circle(Point(0, 0), 10)
        point_edge = Point(10, 0)
        self.assertFalse(circle.contains_point(point_edge))  # edge points not included

    def test_contains_point_returns_false_if_the_specified_point_is_not_within_radius(self):
        circle = Circle(Point(0, 0), 10)
        point_external = Point(20, 0)
        self.assertFalse(circle.contains_point(point_external))

    def test_intersects_returns_true_when_one_circle_inside_the_other(self):
        circle_a = Circle(Point(0, 0), 10)
        circle_b = Circle(Point(0, 0), 5)
        self.assertTrue(circle_a.intersects(circle_b))
        self.assertTrue(circle_b.intersects(circle_a))

    def test_intersects_returns_true_for_two_same_circles(self):
        circle_a = Circle(Point(4, 5), 14)
        circle_b = Circle(Point(4, 5), 14)
        self.assertTrue(circle_a.intersects(circle_b))
        self.assertTrue(circle_b.intersects(circle_a))

    def test_intersects_returns_true_when_two_circles_properly_intersect(self):
        circle_a = Circle(Point(0, 0), 10)
        circle_b = Circle(Point(20, 0), 15)
        self.assertTrue(circle_a.intersects(circle_b))
        self.assertTrue(circle_b.intersects(circle_a))

    def test_intersect_returns_false_when_circles_dont_touch(self):
        circle_a = Circle(Point(0, 0), 10)
        circle_b = Circle(Point(20, 0), 2)
        self.assertFalse(circle_a.intersects(circle_b))
        self.assertFalse(circle_b.intersects(circle_a))

    def test_intersects_returns_false_when_two_circles_touch_with_boarders(self):
        circle_a = Circle(Point(0, 0), 10)
        circle_b = Circle(Point(20, 0), 10)
        self.assertFalse(circle_a.intersects(circle_b))
        self.assertFalse(circle_b.intersects(circle_a))

if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(TestPoint)
#unittest.TextTestRunner(verbosity=2).run(suite)

#@patch('dls_util.shape.Point')
#def setUp(self, MockPoint):
#    self.centre = MockPoint
#    self.centre_new = MockPoint
#    radius = 10
#    self.circle = Circle(self.centre, radius)
#    self.circle_new = Circle(self.centre_new, radius)
# def test_contains_point(self):
#     self.centre_new.distance_to_sq.return_value = 200
#     assert self.circle.contains_point(self.centre_new) == False  # 100 ! < 200
#     self.centre_new.distance_to_sq.return_value = 2
#     assert self.circle.contains_point(self.centre_new) == True  # 2 < 100
#
#
# def test_intersects(self):
#     self.centre.distance_to_sq.return_value = 200
#     assert self.circle.intersects(self.circle_new) == True  # 200 < (10+10)**2 = 400  center_sep_sq < radius_sum_sq
#     self.centre.distance_to_sq.return_value = 400
#     assert self.circle.intersects(self.circle_new) == False  # 400 !< 400  center_sep_sq !< radius_sum_sq