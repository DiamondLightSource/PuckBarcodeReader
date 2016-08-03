import math
from .shape import Point


class Transform:
    """ Represents a transformation on a 2D plane consisting of a translation,
    rotation and scaling.
    """
    def __init__(self, trans, rot, zoom):
        self.trans = trans
        self.rot = rot
        self.zoom = zoom

    def __str__(self):
        return "Translation: {}; Rotation: {:.4f}; Zoom: {:.4f}"\
            .format(self.trans, self.rot, self.zoom)

    def by_offset(self, offset):
        return Transform(self.trans + offset, self.rot, self.zoom)

    def by_rotation(self, angle):
        return Transform(self.trans, self.rot+angle, self.zoom)

    def transform(self, point):
        """ Transform the point by first rotating about the origin, zooming, then
        performing a translation.
        """
        point_ = self._rotate(point, self.rot)
        point_ = self._zoom(point_, self.zoom)
        point_ = self._translate(point_, self.trans)
        return point_

    def reverse(self, point):
        """ Perform a reverse transformation on the point.
        """
        point_ = self._translate(point, self.trans)
        point_ = self._zoom(point_, 1.0/self.zoom)
        point_ = self._rotate(point_, -self.rot)
        return point_

    @staticmethod
    def _rotate(point, a):
        """ Rotate the point about the origin (0,0) """
        x = point.x
        y = point.y
        cos = math.cos(a)
        sin = math.sin(a)
        x_ = x * cos - y * sin
        y_ = x * sin + y * cos
        return Point(x_, y_)

    @staticmethod
    def _zoom(point, scale):
        """ Transform the point by zooming in on the origin (0,0) """
        return Point(point.x*scale, point.y*scale)

    @staticmethod
    def _translate(point, offset):
        """ Translate the point by the specified amount """
        return point + offset

    @staticmethod
    def line_mapping(A, B, A_, B_):
        """ Calculate the transform (rotate then zoom then translate) that
        maps the line AB to the line A'B'.
        """
        # Calculate zoom as the ratio of the lengths of the lines
        scale = A_.distance_to(B_) / A.distance_to(B)

        # Calculate rotation as the difference in the angle from the x axis of the two lines
        old_v_ab = B - A
        old_angle_AB = angle_from_xaxis(old_v_ab)

        new_v_ab = B_ - A_
        new_angle_AB = angle_from_xaxis(new_v_ab)

        rotation_angle = new_angle_AB - old_angle_AB
        if rotation_angle < 0:
            rotation_angle += 2 * math.pi

        # Rotate and zoom point A, then calculate the translation that maps it to A_
        rotated = Transform._rotate(A, rotation_angle)
        zoomed = Transform._zoom(rotated, scale)
        offset = A_ - zoomed

        transform = Transform(offset, rotation_angle, scale)
        return transform

def angle_from_xaxis(v):
    """ Calculate the angle between the x axis and the vector """
    angle = math.atan2(v.x, v.y)
    return angle if angle >= 0 else (2*math.pi + angle)

