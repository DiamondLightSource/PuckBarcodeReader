import math
import unittest
from mock import MagicMock

from dls_barcode.geometry.exception import GeometryAlignmentError
from dls_barcode.geometry.unipuck_calculator import UnipuckCalculator, _partition, calculate_centroid, _center_minimiser


class TestUnipuckCalculator(unittest.TestCase):

    def setUp(self):
        self._slot_centers = MagicMock()  # detected slot centers

    # test perform_alignment
    def test_perform_alignment_raises_error_when_too_many_slots_detected_to_perform_alignment(self):
        self._slot_centers.__len__.return_value = 5
        calculator = self._create_unipuck_calculator()
        with self.assertRaises(GeometryAlignmentError) as cm:
            calculator.perform_alignment()
        self.assertEqual("Not enough slots detected to perform Unipuck alignment", str(cm.exception))

    def test_perform_alignment_raises_error_when_not_enough_slots_detected_to_perform_alignment(self):
        self._slot_centers.__len__.return_value = 100
        calculator = self._create_unipuck_calculator()
        with self.assertRaises(GeometryAlignmentError) as cm:
            calculator.perform_alignment()
        self.assertEqual("Too many slots detected to perform Unipuck alignment", str(cm.exception))

    # test _calculate_puck_alignment
    def test_calculate_puck_alignment_raises_error_when_no_alignment_can_be_done(self):
        self._slot_centers.__len__.return_value = 10
        calculator = self._create_unipuck_calculator()
        with self.assertRaises(GeometryAlignmentError) as cm:
            calculator._calculate_puck_alignment()
        self.assertEqual("Unipuck alignment failed", str(cm.exception))

    #test _partition
    def test_partition_numbers_grouped_around_two_medians_equal_number_of_elements_in_two_groups(self):
        numbers = [1, 2, 3, 4, 5, 10, 12, 13, 14, 15]
        break_point = _partition(numbers)
        self.assertEqual(break_point, 5)

    def test_partition_numbers_grouped_around_two_medians_one_group_larger_than_the_other(self):
        numbers = [1, 2, 10, 12, 13, 14, 15,17]
        break_point = _partition(numbers)
        self.assertEqual(break_point, 2)

    #def test_partition_splits_raises_error_for_empty_slice(self): #I could not find any scenario totriger this exeption
                                                                   #Maybe I don't need it ?
     #   numbers = [1, 2, 3, int(), 5, 10, 12, 13, 15, 14]
     #   with self.assertRaises(GeometryAlignmentError) as cm:
     #       break_point = _partition(numbers)
     #   self.assertEqual("Empty slice", str(cm.exception))

    def test_partition_when_less_than_3_numbers_passed(self):
        #the number is never going to be <3 becouse of other the exeptions in method that calls _partitioning
        numbers = [1, 2]
        with self.assertRaises(Exception) as cm:
            _partition(numbers)
        self.assertEqual("Not enought elements to run partition", str(cm.exception))

    def test_partition_splits_list_of_sequential_numbers(self):
        numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        break_point = _partition(numbers)
        self.assertEqual(break_point, 5)

    #test calculate centroid
    def test_calculate_centroid_returns_average_center_position(self):
        p1 = MagicMock(x = 10, y = 2)
        p2 = MagicMock(x = 20, y = 4)
        points = [p1, p2]
        centroid = calculate_centroid(points)
        self.assertEqual(centroid.x, (p1.x + p2.x)/2)
        self.assertEqual(centroid.y, (p1.y + p2.y)/2)

    #test _center_minimiser
    def test_center_minimiser_returns_0_for_ideal_case(self):
        center = MagicMock()
        point1 = MagicMock()
        point2 = MagicMock()
        point3 = MagicMock()
        point4 = MagicMock()
        #points equally distanced from the center
        point1.distance_to_sq.return_value = 25
        point2.distance_to_sq.return_value = 25
        point3.distance_to_sq.return_value = 25
        point4.distance_to_sq.return_value = 25
        points = [point1, point2, point3, point4]
        e = _center_minimiser(center, points)
        self.assertEqual(e, 0)

    def test_center_minimiser_returns_error_for_point_not_equally_distanced_from_center(self):
        center = MagicMock()
        point1 = MagicMock()
        point2 = MagicMock()
        point3 = MagicMock()
        point4 = MagicMock()
        # points not equally distanced from the center
        point1.distance_to_sq.return_value = 20
        point2.distance_to_sq.return_value = 25
        point3.distance_to_sq.return_value = 50
        point4.distance_to_sq.return_value = 48
        points = [point1, point2, point3, point4]
        e = _center_minimiser(center, points)
        self.assertGreater(e, 0)

    # test _calculate_puck_size
    def test_calculate_puck_size_based_on_seven_pin_centers(self):
        puck_center = MagicMock()
        pin_center = MagicMock()
        pin_center.distance_to.side_effect = [3, 2, 9, 10, 11, 12, 13] #distances of pin_centers to one slot center
        pin_centers = [pin_center] * 7 #initialise an array with 7 pin centers

        puck_radius = UnipuckCalculator._calculate_puck_size(pin_centers, puck_center)

        self.assertEqual(puck_radius, 13)


    # test _determine_puck_orientation
    #a better test coverage could be added
    def test_determine_puck_orientation_first_angle_checked_when_empty_pin_centers_mock_passed(self):
        puck = MagicMock()
        puck.angle.return_value = math.pi/2
        puck.radius.return_value = 12
        first_angle_checked = (90 - 16) / (180 / math.pi)
        pin_centers = MagicMock()
        pin_centers.__len__.return_value = 16 #has to be a number - division by 0

        calculator = self._create_unipuck_calculator()
        orientation = calculator._determine_puck_orientation(puck, pin_centers)
        self.assertEqual(puck.set_rotation.call_count, 33) # checks 32 positions around the initial puck position
        self.assertEqual(orientation, first_angle_checked)

    # test _shortest_sq_distance
    def test_shortest_sq_distance_distance_larger_than_slot_radius(self):
        number_of_puck_slots = 3
        slot_radius = 3
        puck = MagicMock()
        puck.num_slots.return_value = number_of_puck_slots
        puck.slot_radius.return_value = slot_radius

        point = MagicMock()
        point.distance_to_sq.side_effect = [16, 10, 25] #distacne of a point to different slot centers
        #side_effect can also be any iterable object

        sq_dist = UnipuckCalculator._shortest_sq_distance(puck, point)
        self.assertEqual(sq_dist, 10)
        self.assertEqual(point.distance_to_sq.call_count, number_of_puck_slots)

    def test_shortest_sq_distance_distance_smaller_than_slot_radius(self):
        number_of_puck_slots = 3
        slot_radius = 3
        puck = MagicMock()
        puck.num_slots.return_value = number_of_puck_slots
        puck.slot_radius.return_value = slot_radius

        point = MagicMock()
        point.distance_to_sq.side_effect = [4, 6, 10]

        sq_dist = UnipuckCalculator._shortest_sq_distance(puck, point)
        self.assertEqual(sq_dist, 4)
        self.assertEqual(point.distance_to_sq.call_count, 1) #stops after the first slot


    def _create_unipuck_calculator(self):
        return UnipuckCalculator(self._slot_centers)
