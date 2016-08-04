from __future__ import division
import math

from util.shape import Point, Circle
from .unipuck_template import UnipuckTemplate as Template


class Unipuck:
    """ Represents the geometry of a Unipuck within an image including the size, position,
    and orientation and the size and position of the puck's sample slots.
    """
    _SERIAL_DELIM = ":"

    TYPE_NAME = "Unipuck"
    NUM_SLOTS = Template.NUM_SLOTS

    def __init__(self, center, radius, rotation=0.0):
        """ Determine the puck geometry (position and orientation) for the locations of the
        centers of some (or all of the pins).
        """
        self._center = center
        self._radius = radius
        self._rotation = rotation

        self._slot_bounds = []
        self.set_rotation(rotation)

    def center(self): return self._center

    def radius(self): return self._radius

    def angle(self): return self._rotation

    def bounds(self): return Circle(self._center, self._radius)

    def slot_radius(self):
        return self._radius * Template.SLOT_RADIUS

    def slot_bounds(self, slot_num):
        return self._slot_bounds[slot_num - 1]

    def center_radius(self):
        return self._radius * Template.CENTER_RADIUS

    def center_bounds(self):
        return Circle(self._center, self.center_radius())

    def num_slots(self):
        return Unipuck.NUM_SLOTS

    def slot_center(self, slot_num):
        return self._slot_bounds[slot_num - 1].center()

    def containing_slot(self, point):
        """ Returns the number of the slot which contains the specified point or None otherwise. """
        for i, bounds in enumerate(self._slot_bounds):
            if bounds.contains_point(point):
                return i + 1

        return None

    def set_rotation(self, angle):
        """ Set the orientation of the puck to the specified angle. Recalculate the
        positions of the slots.
        """
        self._rotation = angle

        # Calculate pin slot locations
        layer_counts = Template.N
        layer_radii = Template.LAYER_RADII

        center = self._center

        self._slot_bounds = []
        for i, layer_count in enumerate(layer_counts):
            layer_radius = layer_radii[i] * self._radius

            for j in range(layer_count):
                angle = (2.0 * math.pi * -j / layer_count) - (math.pi / 2.0) + self._rotation
                x = int(center.x + layer_radius * math.cos(angle))
                y = int(center.y + layer_radius * math.sin(angle))
                slot_center = Point(x, y)
                bounds = Circle(slot_center, self.slot_radius())
                self._slot_bounds.append(bounds)

    ############################
    # Drawing Functions
    ############################
    def draw_plate(self, img, color):
        """ Draws an outline of the puck on the supplied image including the locations of the slots. """
        img.draw_dot(self._center, color)
        img.draw_circle(self.bounds(), color, thickness=int(0.05 * self._radius))
        img.draw_circle(self.center_bounds(), color)
        for bounds in self._slot_bounds:
            img.draw_dot(bounds.center(), color)
            img.draw_circle(bounds, color)

    def draw_pin_highlight(self, img, color, pin_number):
        """ Draws a highlight circle and slot number for the specified slot on the image. """
        bounds = self._slot_bounds[pin_number - 1]
        img.draw_circle(bounds, color, thickness=int(bounds.radius() * 0.2))
        img.draw_text(str(pin_number), bounds.center(), color, centered=True)

    def crop_image(self, img):
        """ Crops the image to the area which contains the puck. """
        img.crop_image(self._center, 1.1 * self._radius)

    ############################
    # Serialization
    ############################
    @staticmethod
    def deserialize(string):
        tokens = string.split(Unipuck._SERIAL_DELIM)

        center = Point(int(tokens[0]), int(tokens[1]))
        radius = int(tokens[2])
        angle = float(tokens[3])

        return Unipuck(center, radius, angle)

    def serialize(self):
        tokens = [str(self._center.x), str(self._center.y), str(self._radius), str(self._rotation)]
        return self._SERIAL_DELIM.join(tokens)

    def to_string(self):
        return "center: ({}, {}); radius: {}; rotation: {:.3f}".format(
            self._center.x, self._center.y, self._radius, self._rotation)
