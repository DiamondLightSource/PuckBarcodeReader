from __future__ import division

import math
from .point import Point


class Circle:
    def __init__(self, center, radius):
        self._center = center
        self._radius = radius

    def __str__(self):
        """ String representation of the circle. """
        return "Circle - center = ({:.2f}, {:.2f}); radius = {:.2f}".format(self.x(), self.y(), self._radius)

    def center(self):
        return self._center

    def radius(self):
        return self._radius

    def x(self):
        return self._center.x

    def y(self):
        return self._center.y

    def diameter(self):
        return self._radius * 2

    def circumference(self):
        return 2 * math.pi * self._radius

    def area(self):
        return math.pi * (self._radius ** 2)

    def offset(self, point):
        """ Returns a new circle which is the same size as this one but offset (moved by the specified amount). """
        return Circle(self._center + point, self._radius)

    def scale(self, factor):
        """ Returns a new circle which is a scaled version of this one. """
        return Circle(self._center, self._radius * factor)

    def contains_point(self, point):
        """ Returns true if the specified point is within the Circle's radius"""
        radius_sq = self._radius ** 2
        distance_sq = point.distance_to_sq(self._center)
        return distance_sq < radius_sq

    def intersects(self, circle):
        """ Returns true if the two circles intersect. """
        center_sep_sq = self._center.distance_to_sq(circle.center())
        radius_sum_sq = (self.radius() + circle.radius()) ** 2
        return center_sep_sq < radius_sum_sq

    def serialize(self):
        return "{}:{}:{}".format(self.x(), self.y(), self._radius)

    @staticmethod
    def deserialize(string):
        tokens = string.split(":")
        x = float(tokens[0])
        y = float(tokens[1])
        r = float(tokens[2])
        center = Point(x, y)
        return Circle(center, r)