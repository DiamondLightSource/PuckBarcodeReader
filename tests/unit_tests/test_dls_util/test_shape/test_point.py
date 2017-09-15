import unittest

from dls_util.shape import Point


class TestPoint(unittest.TestCase):

    def setUp(self):
        self.point = Point(0.0, 2.0)
        self.first_point = Point(0.0, 1.0)
        self.second_point = Point(2.0, 2.0)
        self.third_point = Point(2.0, 1.0)

    def test_maths_works(self):
        self.assertEqual(self.first_point.distance_to(self.second_point - self.third_point), 0.0)

    def test_length_sq(self):
        self.assertEquals(Point.length_sq(self.point), 4.0)

    def test_length(self):
        self.assertEquals(Point.length(self.point), 2.0)

    def test_distance_to(self):
        self.assertEquals(self.point.distance_to(self.first_point), 1.0)
        self.assertEquals(self.point.distance_to(self.second_point), 2.0)

    def test_distance_to_sq(self):
        self.assertEquals(self.point.distance_to_sq(self.first_point), 1.0)
        self.assertEquals(self.point.distance_to_sq(self.second_point), 4.0)

    def test_length(self):
        scaled = Point.scale(self.third_point, 2)
        self.assertEquals(scaled.x, 4.0)
        self.assertEquals(scaled.y, 2.0)

    def test_floatify(self):
        to_float = self.third_point.floatify()
        self.assertEquals(to_float.x, float(2.0))
        self.assertEquals(to_float.y, float(1.0))

    def test_intify(self):
        to_int = self.third_point.intify()
        self.assertEquals(to_int.x, int(2.0))
        self.assertEquals(to_int.y, int(1.0))

if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(TestPoint)
#unittest.TextTestRunner(verbosity=2).run(suite)