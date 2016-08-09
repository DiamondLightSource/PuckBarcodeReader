from dls_barcode.util.image import Color
from dls_barcode.util.shape import Circle


class FinderPattern:
    """A representation of the location of a Datamatrix 'finder pattern'
    in an image. All points and lengths are in units of Pixels"""

    def __init__(self, corner, vec_base, vec_side):
        self.corner = corner
        self.baseVector = vec_base
        self.sideVector = vec_side

        # Lengths of the two arms
        self.baseLength = vec_base.length()
        self.sideLength = vec_side.length()

        # positions of the three corners
        self.c1 = corner
        self.c2 = corner + vec_base
        self.c3 = corner + vec_side

        # Position of center of the datamatrix in image pixels
        self.center = (corner + ((vec_base + vec_side) / 2.0)).intify()

        # Radius of datamatrix (distance from center to a corner) in pixels
        self.radius = corner.distance_to(self.center)

    def point_in_radius(self, point):
        return self.bounds().contains_point(point)

    def bounds(self):
        return Circle(self.center, self.radius)

    def draw_to_image(self, image, color=None):
        if color is None:
            color = Color.Green()
        image.draw_line(self.c1, self.c2, color, 1)
        image.draw_line(self.c3, self.c1, color, 1)

    def correct_lengths(self, expected_length):
        """ Return a new finder pattern that is in the same position as this one but with
        base/side being the same length. """

        if abs(self.baseLength - expected_length) < abs(self.sideLength - expected_length):
            factor = self.baseLength / self.sideLength
            new_base_vec = self.baseVector
            new_side_vec = self.sideVector * factor
        else:
            factor = self.sideLength / self.baseLength
            new_base_vec = self.baseVector * factor
            new_side_vec = self.sideVector

        return FinderPattern(self.corner, new_base_vec, new_side_vec)
