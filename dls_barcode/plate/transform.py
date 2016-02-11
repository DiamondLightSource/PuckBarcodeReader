import math

class Transform:
    def __init__(self, x, y, rot, zoom):
        self.x = x
        self.y = y
        self.rot = rot
        self.zoom = zoom

    def __str__(self):
        return "Horizontal: {:.4f}; Vertical: {:.4f}; Rotation: {:.4f}; Zoom: {:.4f}"\
            .format(self.x, self.y, self.rot, self.zoom)

    def transform(self, point):
        """ Transform the point by first rotating about the origin then
        performing a translation
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
        x = point[0]
        y = point[1]
        cos = math.cos(a)
        sin = math.sin(a)
        x_ = x * cos - y * sin
        y_ = x * sin + y * cos
        return (x_, y_)

    @staticmethod
    def _zoom(point, scale):
        return (point[0]*scale, point[1]*scale)

    @staticmethod
    def _translate(point, offset):
        return (point[0] + offset[0], point[1] + offset[1])

    @staticmethod
    def line_mapping(A, B, A_, B_):
        """ Calculate the transform (rotate then zoom then translate) that
        maps the line AB to the line A'B'.
        """
        # determine zoom
        scale = distance(A_, B_) / distance(A, B)

        old_v_ab = vec_minus(B, A)
        old_angle_AB = angle_from_xaxis(old_v_ab)

        new_v_ab = vec_minus(B_, A_)
        new_angle_AB = angle_from_xaxis(new_v_ab)

        rotation_angle = new_angle_AB-old_angle_AB
        if rotation_angle < 0: rotation_angle = 2 * math.pi + rotation_angle

        rotated = Transform._rotate(A, rotation_angle)
        zoomed = Transform._zoom(rotated, scale)
        offset = vec_minus(A_, zoomed)

        transform = Transform(offset[0], offset[1], rotation_angle, scale)
        return transform




def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def vec_minus(b, a):
    return (b[0]-a[0], b[1]-a[1])


def angle_from_xaxis(v):
    angle = math.atan2(v[1], v[0])
    return angle if angle >= 0 else (2*math.pi + angle)

