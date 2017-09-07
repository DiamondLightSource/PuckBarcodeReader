import unittest
from mock import MagicMock, patch

from dls_util.shape import Circle


class TestCircle(unittest.TestCase):

    @patch('dls_util.shape.Point')
    def setUp(self, MockPoint):
        self.centre = MockPoint
        self.centre_new = MockPoint
        radius = 10
        self.circle = Circle(self.centre, radius)
        self.circle_new = Circle(self.centre_new, radius)


    def test_contains_point(self):
        self.centre_new.distance_to_sq.return_value = 200
        assert self.circle.contains_point(self.centre_new) == False #100 ! < 200
        self.centre_new.distance_to_sq.return_value = 2
        assert self.circle.contains_point(self.centre_new) == True  # 2 < 100

    def test_intersects(self):
        self.centre.distance_to_sq.return_value = 200
        assert self.circle.intersects(self.circle_new) == True  # 200 < (10+10)**2 = 400  center_sep_sq < radius_sum_sq
        self.centre.distance_to_sq.return_value = 400
        assert self.circle.intersects(self.circle_new) == False # 400 !< 400  center_sep_sq !< radius_sum_sq



if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(TestPoint)
#unittest.TextTestRunner(verbosity=2).run(suite)