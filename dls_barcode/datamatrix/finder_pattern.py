import math


class FinderPattern:
    """A representation of the location of a Datamatrix 'finder pattern'
    in an image. All points and lengths are in units of Pixels"""

    def __init__(self, corner, vec_base, vec_side):
        self.corner = [int(round(corner[0])), int(round(corner[1]))]
        self.baseVector = [int(round(vec_base[0])), int(round(vec_base[1]))]
        self.sideVector = [int(round(vec_side[0])), int(round(vec_side[1]))]

        # Lengths of the two arms
        self.baseLength = math.sqrt(vec_base[0]**2 + vec_base[1]**2)
        self.sideLength = math.sqrt(vec_side[0]**2 + vec_side[1]**2)

        # positions of the three corners
        self.c1 = (corner[0], corner[1])
        self.c2 = (corner[0]+vec_base[0], corner[1]+vec_base[1])
        self.c3 = (corner[0]+vec_side[0], corner[1]+vec_side[1])

        # Position of center of the datamatrix in image pixels
        self.center = (int(round(corner[0] + (vec_base[0] + vec_side[0]) / 2)),
                       int(round(corner[1] + (vec_base[1] + vec_side[1]) / 2)))

        # Radius of datamatrix (distance from center to a corner) in pixels
        self.radius = int(math.sqrt((vec_base[0]*vec_base[0] + vec_base[1]*vec_base[1])/2))

    def pack(self):
        return tuple([self.corner, self.baseVector, self.sideVector])

    def point_in_radius(self, point):
        return (point[0] - self.center[0])**2 + (point[1] - self.center[1])**2 < self.radius

    def bounds(self):
        return (self.center, self.radius)

    def draw_to_image(self, image, color=None):
        from dls_barcode.util.image import Image
        if color is None:
            color = Image.GREEN
        image.draw_line(self.c1, self.c2, color, 1)
        image.draw_line(self.c3, self.c1, color, 1)

    def correct_lengths(self, expected_length):
        """ Return a new finder pattern that is in the same position as this one but with
        base/side being the same length. """

        if abs(self.baseLength - expected_length) < abs(self.sideLength - expected_length):
            factor = self.baseLength / self.sideLength
            new_base_vec = self.baseVector
            new_side_vec = [self.sideVector[0]*factor, self.sideVector[1]*factor]
        else:
            factor = self.sideLength / self.baseLength
            new_base_vec = [self.baseVector[0]*factor, self.baseVector[1]*factor]
            new_side_vec = self.sideVector

        return FinderPattern(self.corner, new_base_vec, new_side_vec)
