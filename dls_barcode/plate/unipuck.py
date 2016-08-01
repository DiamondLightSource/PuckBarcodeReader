from __future__ import division
import math


class UnipuckTemplate:
    """ Defines the layout of a type of sample holder that is a circular puck
    that contains concentric circles (layers) of sample pins.
    """
    NUM_SLOTS = 16
    PUCK_RADIUS = 1
    CENTER_RADIUS = 0.151  # radius of puck center (relative to puck radius)
    SLOT_RADIUS = 0.197  # radius of a pin slot (relative to puck radius)
    LAYERS = 2  # number of concentric layers of pin slots
    N = [5, 11]  # number of pin slots in each concentric layer, starting from center
    LAYER_RADII = [0.371, 0.788]  # distance of center of a pin of a given concentric layer from center of puck


class Unipuck:
    """ Represents the geometry of a Unipuck within an image including the size, position,
    and orientation and the size and position of the puck's sample slots.
    """
    def __init__(self, center, radius, rotation=0.0):
        """ Determine the puck geometry (position and orientation) for the locations of the
        centers of some (or all of the pins).
        """
        self._center = center
        self._radius = radius
        self._rotation = rotation

        self._slot_centers = []
        self.set_rotation(rotation)

        self._aligned = False

    def center(self): return self._center

    def radius(self): return self._radius

    def angle(self): return self._rotation

    def slot_radius(self):
        return self._radius * UnipuckTemplate.SLOT_RADIUS

    def center_radius(self):
        return self._radius * UnipuckTemplate.CENTER_RADIUS

    def num_slots(self):
        return UnipuckTemplate.NUM_SLOTS

    def is_aligned(self):
        """ True if the puck geometry has been successfully aligned to the image. """
        return self._aligned

    def set_aligned(self, value): self._aligned = value

    def slot_center(self, slot_num):
        return self._slot_centers[slot_num - 1]

    def slot_bounds(self, slot_num):
        center = self.slot_center(slot_num)
        return center, self.slot_radius()

    def containing_slot(self, point):
        """ Returns the number of the slot which contains the specified point or 0 otherwise. """
        slot_sq = self.slot_radius() ** 2
        for i, center in enumerate(self._slot_centers):
            # slots are non-overlapping so if its in the slot radius, it must be the closest
            distance_sq = (center[0] - point[0]) ** 2 + (center[1] - point[1]) ** 2
            if distance_sq < slot_sq:
                return i + 1

        return None

    def set_rotation(self, angle):
        """ Set the orientation of the puck to the specified angle. Recalculate the
        positions of the slots.
        """
        self._rotation = angle

        # Calculate pin slot locations
        n = UnipuckTemplate.N
        r = UnipuckTemplate.LAYER_RADII

        center = self._center

        self._slot_centers = []
        for i, num in enumerate(n):
            radius = r[i] * self._radius
            for j in range(num):
                angle = (2.0 * math.pi * -j / num) - (math.pi / 2.0) + self._rotation
                point = tuple([int(center[0] + radius * math.cos(angle)), int(center[1] + radius * math.sin(angle))])
                self._slot_centers.append(point)

    ############################
    # Drawing Functions
    ############################
    def draw_plate(self, cvimg, color):
        """ Draws an outline of the puck on the supplied image including the locations of the slots. """
        cvimg.draw_dot(self._center, color)
        cvimg.draw_circle(self._center, self._radius, color, thickness=int(0.05 * self._radius))
        cvimg.draw_circle(self._center, self.center_radius(), color)
        for center in self._slot_centers:
            cvimg.draw_dot(center, color)
            cvimg.draw_circle(center, self.slot_radius(), color)

    def draw_pin_highlight(self, cvimg, color, pin_number):
        """ Draws a highlight circle and slot number for the specified slot on the image. """
        center = self._slot_centers[pin_number - 1]
        cvimg.draw_circle(center, self.slot_radius(), color, thickness=int(self.slot_radius() * 0.2))
        cvimg.draw_text(str(pin_number), center, color, centered=True)

    def crop_image(self, cvimg):
        """ Crops the image to the area which contains the puck. """
        cvimg.crop_image(self._center, 1.1 * self._radius)

    ############################
    # Factory
    ############################
    @staticmethod
    def from_center_and_pin6(center, pin6_center):
        x = center[0] - pin6_center[0]
        y = center[1] - pin6_center[1]
        length = math.sqrt(x**2+y**2)
        radius = int(length / UnipuckTemplate.LAYER_RADII[1])

        angle = math.atan2((pin6_center[0] - center[0]), (center[1] - pin6_center[1]))
        puck = Unipuck(center, radius, angle)

        return puck
