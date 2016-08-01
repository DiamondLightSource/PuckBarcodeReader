from __future__ import division

import math


class Point:
    """ Represents a point in a 2D Cartesian coordinate system.
    """
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __neg__(self):
        """ Unary minus operator. """
        return Point(-self.x, -self.y)

    def __add__(self, p):
        """ PointA + PointB addition operator. """
        return Point(self.x+p.x, self.y+p.y)

    def __sub__(self, p):
        """ PointA - PointB subtraction operator. """
        return Point(self.x-p.x, self.y-p.y)

    def __mul__(self, scalar):
        """ PointA * scalar multiplication operator. """
        return Point(self.x*scalar, self.y*scalar)

    def __div__(self, scalar):
        """ PointA / scalar division operator. """
        return Point(self.x/scalar, self.y/scalar)

    def __floordiv__(self, scalar):
        """ PointA / scalar integer division operator. """
        return Point(self.x//scalar, self.y//scalar)

    def __truediv__(self, scalar):
        """ PointA / scalar true (float) division operator. """
        return Point(self.x/scalar, self.y/scalar)

    def __str__(self):
        """ Human-readable string representation. """
        return "({:.2f}, {:.2f})".format(self.x, self.y)

    def __repr__(self):
        """ Unambiguous string representation. """
        return "{}({}, {})".format(self.__class__.__name__, self.x, self.y)

    def length(self):
        """ Distance from the origin to the point. """
        return math.sqrt(self.length_sq())

    def length_sq(self):
        """ Square of the distance from the origin to the point. """
        return self.x**2 + self.y**2

    def distance_to(self, p):
        """ Distance between the two points. """
        return (self - p).length()

    def distance_to_sq(self, p):
        """ Square of the distance between the two points. """
        return (self - p).length_sq()

    def scale(self, factor):
        """ Returns a scaled version of the Point (from the origin). """
        return Point(self.x*factor, self.y*factor)

    def intify(self):
        """ Return a new point which is the same as this but with (rounded) integer coordinates. """
        return Point(int(round(self.x, 0)), int(round(self.y, 0)))

    def floatify(self):
        """ Return a new point which is the same as this but with float coordinates. """
        return Point(float(self.x), float(self.y))

    def tuple(self):
        """ Return the coordinates as an (x, y) tuple. """
        return self.x, self.y

    @staticmethod
    def from_array(arr):
        """ Create a new point from a length-2 array of x,y coordinates. """
        return Point(arr[0], arr[1])


