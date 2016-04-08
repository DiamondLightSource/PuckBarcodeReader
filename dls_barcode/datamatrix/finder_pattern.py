import math


class FinderPattern():
    """A representation of the location of a Datamatrix 'finder pattern'
    in an image. All points and lengths are in units of Pixels"""

    def __init__(self, x_corner, vec_base, vec_side):
        self.corner = x_corner
        self.baseVector = vec_base
        self.sideVector = vec_side

        # positions of the three corners
        self.c1 = tuple(x_corner)
        self.c2 = tuple(x_corner + vec_base)
        self.c3 = tuple(x_corner + vec_side)

        # Position of center of the datamatrix in image pixels
        self.center = tuple(map(int, x_corner + (vec_base + vec_side)/2))

        # Radius of datamatrix (distance from center to a corner) in pixels
        self.radius = int(math.sqrt((vec_base[0]*vec_base[0] + vec_base[1]*vec_base[1])/2))

    def pack(self):
        return tuple([self.corner, self.baseVector, self.sideVector])

    def point_in_radius(self, point):
        return (point[0] - self.center[0])**2 + (point[1] - self.center[1])**2 < self.radius

    def bounds(self):
        return (self.center, self.radius)

    def draw_to_image(self, image):
        from dls_barcode.util.image import Image
        image.draw_line(self.c1, self.c2, Image.GREEN, 1)
        image.draw_line(self.c3, self.c1, Image.GREEN, 1)