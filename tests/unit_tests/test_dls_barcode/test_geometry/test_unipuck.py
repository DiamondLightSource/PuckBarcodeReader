import unittest
from mock import MagicMock
import math

from dls_barcode.geometry.unipuck import Unipuck
from dls_util.shape import Point


class TestUnipuck(unittest.TestCase):

    #def setUp(self):
        #Template = MagicMock()

    def test_slot_radius_calculates_radius_in_relation_to_template_radius(self):
        center = MagicMock()
        uni1 = Unipuck(center, 100)
        r1 = uni1.slot_radius()
        uni2 = Unipuck(center,1)
        r2 = uni2.slot_radius()

        self.assertTrue(r1 != 100)
        self.assertTrue(r2 != 1)
        self.assertTrue(math.ceil(r1/r2) == 100)

    def test_center_radius_calculates_radius_in_relation_to_template_radius(self):
        center = MagicMock()
        uni1 = Unipuck(center, 100)
        r1 = uni1.center_radius()
        uni2 = Unipuck(center,1)
        r2 = uni2.center_radius()

        self.assertTrue(r1 != 100)
        self.assertTrue(r2 != 1)
        self.assertTrue(math.ceil(r1/r2) == 100)

    def test_containing_slot_returns_the_number_of_slot_to_which_a_point_belongs(self):
        #this method assumes that the slot bounds (objects of type circle) are always stored
        # in a particular sequence in slot_bounds array
        #TODO: posssible improvement: create a slot bound class with slot number parameter
        uni1 = Unipuck(center=MagicMock(), radius=MagicMock())
        slot_bound = MagicMock()
        slot_bound.contains_point.return_value = False

        slot_bound1 = MagicMock()
        slot_bound1.contains_point.return_value = False

        slot_bound2 = MagicMock()
        slot_bound2.contains_point.return_value = True

        uni1._slot_bounds = [slot_bound, slot_bound1, slot_bound2]
        number = uni1.containing_slot(MagicMock())
        self.assertTrue(number == 3)

    def test_containing_slot_returns_None_if_no_bounds(self):
        uni1 = Unipuck(center=MagicMock(), radius=MagicMock())
        uni1._slot_bounds = []
        number = uni1.containing_slot(MagicMock())
        self.assertIsNone(number)

    def test_containing_slot_returns_None_if_point_does_not_belong_to_any_bound(self):
        uni1 = Unipuck(center=MagicMock(), radius=MagicMock())
        slot_bound = MagicMock()
        slot_bound.contains_point.return_value = False

        slot_bound1 = MagicMock()
        slot_bound1.contains_point.return_value = False

        uni1._slot_bounds = [slot_bound, slot_bound1]
        number = uni1.containing_slot(MagicMock())
        self.assertIsNone(number)


    def test_calculate_slot_bounds_returns_x0_for_slots1and6_if_rotation_and_center_are_0(self):
        #again the assumption that slot bounds have a particular sequence - slot bound[0] is slot number 1
        center = Point(0,0)
        rotation = 0
        radius = 10

        slot_bounds = Unipuck.calculate_slot_bounds(center,radius,rotation)
        self.assertTrue(len(slot_bounds)==16)
        slot1 = slot_bounds[0]
        self.assertTrue(slot1.center().x == 0)
        slot6 = slot_bounds[5]
        self.assertTrue(slot6.center().x == 0)

