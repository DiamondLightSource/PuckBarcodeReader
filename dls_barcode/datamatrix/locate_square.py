from __future__ import division

import math
import cv2
import numpy as np

from .finder_pattern import FinderPattern
from dls_barcode.util import Transform, Image


class SquareLocator:
    """ Utility to locate a single datamatrix finder pattern in a small image in which the datamatrix
    is located roughly in the middle of the image, but at any orientation. """

    def __init__(self):
        self.metric_cache = dict()
        pass

    def locate(self, gray_img, barcode_size):
        """ Get the finder pattern of the datamatrix of the specified side length. """
        # Clear cache
        self.metric_cache = dict()

        # Threshold the image converting it to a binary image
        thresh_img = self._adaptive_threshold(gray_img.img, 99, 0)

        best_transform = self._minimise_integer_grid(thresh_img, gray_img.center(), barcode_size)

        # Get the finder pattern
        fp = self._locate_finder_in_square(thresh_img, best_transform, barcode_size)

        return fp


    def _adaptive_threshold(self, image, blocksize, C):
        """ Perform an adaptive threshold operation on the image, reducing it to a binary image.
        """
        thresh = cv2.adaptiveThreshold(image, 255.0,
            cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blocksize, C)

        return Image(None, thresh)


    def _minimise_integer_grid(self, thresh_img, center, side_length):
        """ Attempt to locate the square area (of the specified size, centered on the specified
        center point) in the binary image which has the minimum brightness.

        The datamatrix is a relatively dark area on a relative light background, so the area
        corresponding to the datamatrix should have the lowest brightness.
        """
        done = False

        initial_transform = Transform(int(center[0]), int(center[1]), 0, 1)
        best_val = 1000000000000000
        best_trs = initial_transform

        while not done:
            kings = self._make_iteration_transforms(initial_transform)
            for trs in kings:
                val = self._calculate_average_brightness(thresh_img, trs, side_length)
                if val < best_val:
                    best_val = val
                    best_trs = trs

            if best_trs == initial_transform:
                done = True

            initial_transform = best_trs

        return best_trs

    def _make_iteration_transforms(self, transform):
        """ Create a selection of transforms that differ slightly from the supplied transform.
        """
        kings = []
        grid_points = [-5, -3, -1, 0, 1, 3, 5]
        angle_points = [-10, -5, -1, 0, 1, 5, 10]
        for x in grid_points:
            for y in grid_points:
                for degrees in angle_points:
                    radians = degrees * math.pi / 180
                    trs = transform.by_offset(x, y)
                    trs = trs.by_rotation(radians )
                    kings.append(trs)

        return kings

    def _calculate_average_brightness(self, image, transform, size):
        """ For the square area (defined by the transform and size) in the binary
        image, calculate the average brightness per pixel.

        The datamatrix is a relatively dark area on a relative light background,
        so a lower average brightness corresponds to a greater likelihood of the
        area being the datamatrix.
        """
        cx, cy = transform.x, transform.y
        center = (cx, cy)
        angle = transform.rot

        # Create cache key
        key = (angle, center)

        # If this x,y,angle combination has been seen before, retrieve the previous cached result
        if key in self.metric_cache:
            brightness = self.metric_cache[key]

        else:
            rotated = image.rotate(angle, center)

            x1, y1 = int(round(cx-size/2)), int(round(cy-size/2))
            x2, y2 = int(round(x1 + size)), int(round(y1 + size))

            brightness = np.sum(rotated.img[y1:y2, x1:x2]) / (size * size)

            # Store in dictionary
            self.metric_cache[key] = brightness

        return brightness

    def _locate_finder_in_square(self, image, transform, size):
        """ For the located barcode in the image, identify which of the sides make
        up the finder pattern.
        """
        radius = int(round(size/2))
        cx,cy = transform.x, transform.y
        angle = transform.rot

        rotated = image.rotate(angle, (cx,cy))

        sx1, sy1 = cx-radius, cy-radius
        sx2, sy2 = cx+radius, cy+radius
        thick = int(round(size / 14))

        # Top
        x1, y1 = sx1, sy1
        x2, y2 = sx2, sy1 + thick
        top = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Left
        x1, y1 = sx1, sy1
        x2, y2 = sx1 + thick, sy2
        left = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Bottom
        x1, y1 = sx1, sy2 - thick
        x2, y2 = sx2, sy2
        bottom = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Right
        x1, y1 = sx2 - thick, sy1
        x2, y2 = sx2, sy2
        right = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Identify finder edges
        if top < bottom and left < right:
            c1 = [sx1, sy1]
            c2 = [sx1, sy2]
            c3 = [sx2, sy1]
            print("Top-Left")
        elif top < bottom and right < left:
            c1 = [sx2, sy1]
            c2 = [sx1, sy1]
            c3 = [sx2, sy2]
            print("Top-Right")
        elif bottom < top and left < right:
            c1 = [sx1, sy2]
            c2 = [sx2, sy2]
            c3 = [sx1, sy1]
            print("Bottom-Left")
        elif bottom < top and right < left:
            c1 = [sx2, sy2]
            c2 = [sx2, sy1]
            c3 = [sx1, sy2]
            print("Bottom-Right")
        else:
            raise NotImplementedError

        # rotate points around center of square
        center = (cx,cy)
        c1 = _rotate_around_point(c1,angle,center)
        c2 = _rotate_around_point(c2,angle,center)
        c3 = _rotate_around_point(c3,angle,center)

        # Create finder pattern
        c1 = (int(c1[0]), int(c1[1]))
        side1 = (int(c2[0]-c1[0]), int(c2[1]-c1[1]))
        side2 = (int(c3[0]-c1[0]), int(c3[1]-c1[1]))
        fp = FinderPattern(c1,side1,side2)

        return fp


def _rotate_around_point(point, angle, center):
    """ Rotate the point about the center position """
    x = point[0] - center[0]
    y = point[1] - center[1]
    cos = math.cos(angle)
    sin = math.sin(angle)
    x_ = x * cos - y * sin
    y_ = x * sin + y * cos
    return (x_+center[0], y_+center[1])