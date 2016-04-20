import math


class Transform:
    """ Represents a transformation on a 2D plane consisting of a translation,
    rotation and scaling.
    """
    def __init__(self, x, y, rot, zoom):
        self.x = x
        self.y = y
        self.rot = rot
        self.zoom = zoom

    def __str__(self):
        return "Horizontal: {:.4f}; Vertical: {:.4f}; Rotation: {:.4f}; Zoom: {:.4f}"\
            .format(self.x, self.y, self.rot, self.zoom)

    def by_offset(self, x, y):
        return Transform(self.x+x, self.y+y, self.rot, self.zoom)

    def by_rotation(self, angle):
        return Transform(self.x, self.y, self.rot+angle, self.zoom)

    def transform(self, point):
        """ Transform the point by first rotating about the origin, zooming, then
        performing a translation.
        """
        point_ = self._rotate(point, self.rot)
        point_ = self._zoom(point_, self.zoom)
        point_ = self._translate(point_, (self.x, self.y))
        return point_

    def reverse(self, point):
        """ Perform a reverse transformation on the point.
        """
        point_ = self._translate(point, (-self.x, -self.y))
        point_ = self._zoom(point_, 1.0/self.zoom)
        point_ = self._rotate(point_, -self.rot)
        return point_



    @staticmethod
    def _rotate(point, a):
        """ Rotate the point about the origin (0,0) """
        x = point[0]
        y = point[1]
        cos = math.cos(a)
        sin = math.sin(a)
        x_ = x * cos - y * sin
        y_ = x * sin + y * cos
        return (x_, y_)

    @staticmethod
    def _zoom(point, scale):
        """ Transform the point by zooming in on the origin (0,0) """
        return (point[0]*scale, point[1]*scale)

    @staticmethod
    def _translate(point, offset):
        """ Translate the point by the specified amount """
        return (point[0] + offset[0], point[1] + offset[1])

    @staticmethod
    def line_mapping(A, B, A_, B_):
        """ Calculate the transform (rotate then zoom then translate) that
        maps the line AB to the line A'B'.
        """
        # Calculate zoom as the ratio of the lengths of the lines
        scale = distance(A_, B_) / distance(A, B)

        # Calculate rotation as the difference in the angle from the x axis of the two lines
        old_v_ab = vec_minus(B, A)
        old_angle_AB = angle_from_xaxis(old_v_ab)

        new_v_ab = vec_minus(B_, A_)
        new_angle_AB = angle_from_xaxis(new_v_ab)

        rotation_angle = new_angle_AB-old_angle_AB
        if rotation_angle < 0: rotation_angle = 2 * math.pi + rotation_angle

        # Rotate and zoom point A, then calculate the transwlation that maps it to A_
        rotated = Transform._rotate(A, rotation_angle)
        zoomed = Transform._zoom(rotated, scale)
        offset = vec_minus(A_, zoomed)

        transform = Transform(offset[0], offset[1], rotation_angle, scale)
        return transform


def distance(a, b):
    """ Calculate the Euclidean distance between the two points """
    return math.hypot(a[0] - b[0], a[1] - b[1])


def vec_minus(b, a):
    """ Subtract vector a from vector b"""
    return (b[0]-a[0], b[1]-a[1])


def angle_from_xaxis(v):
    """ Calculate the angle between the x axis and the vector """
    angle = math.atan2(v[1], v[0])
    return angle if angle >= 0 else (2*math.pi + angle)

