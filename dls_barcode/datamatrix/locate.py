from __future__ import division

import math
import numpy as np

from .locate_square import SquareLocator
from .locate_contour import ContourLocator


class Locator:
    def __init__(self):
        # Assume that all datamatricies are roughly the same
        #   size so filter out any obviously mis-sized ones
        self._median_radius_tolerance = 0.3
        self._median_radius = 0
        self._image = None

    def locate_shallow(self, img):
        # Locate finder patterns in whole image
        finder_patterns = self._contours_shallow(img)

        # Filter out any which differ significantly in size
        if len(finder_patterns) > 3:
            self._median_radius = np.median([fp.radius for fp in finder_patterns])
            finder_patterns = list(filter(self._filter_median_radius, finder_patterns))

        # Filter out patterns that overlap
        valid_patterns = []
        for fp in finder_patterns:
            in_radius = False
            for ex in valid_patterns:
                in_radius = in_radius | ex.point_in_radius(fp.center)
            if not in_radius:
                valid_patterns.append(fp)

        return valid_patterns

    def locate_deep(self, img, expected_radius):
        self._median_radius = expected_radius
        self._image = img

        finder_patterns = self._contours_deep(img)
        finder_patterns = list(filter(self._filter_image_edges, finder_patterns))
        finder_patterns = list(filter(self._filter_median_radius, finder_patterns))

        # If the fps are asymmetrical, correct the side lengths
        side = expected_radius * (2 / math.sqrt(2))
        finder_patterns = [fp.correct_lengths(side) for fp in finder_patterns]

        return finder_patterns

    def locate_square(self, img, side_length):
        finder_pattern = SquareLocator().locate(img, side_length)
        return finder_pattern

    @staticmethod
    def _contours_shallow(img):
        c_values = [16, 8]
        morph_size = 3
        block_size = 35

        # Use a couple of different values of C as much more likely to locate the finder patterns
        finder_patterns = []
        for C in c_values:
            fps = ContourLocator().locate_datamatrices(img, block_size, C, morph_size)
            finder_patterns.extend(fps)

        return finder_patterns

    @staticmethod
    def _contours_deep(img):
        c_values = [0, 4, 20, 16, 8]
        morph_sizes = [3, 2]
        block_size = 35

        # Use a couple of different values of C as much more likely to locate the finder patterns
        finder_patterns = []
        for ms in morph_sizes:
            for C in c_values:
                fps = ContourLocator().locate_datamatrices(img, block_size, C, ms)
                finder_patterns.extend(fps)

        return finder_patterns

    def _filter_median_radius(self, fp):
        """Return true iff finder pattern radius is close to the median"""
        median = self._median_radius
        tolerance = self._median_radius_tolerance * median
        return (median - tolerance) < fp.radius < (median + tolerance)

    def _filter_image_edges(self, fp):
        """Return true if the finder pattern isn't right along on of the edges of the image.
        This is needed because the algorithm sometimes detects the edge of the image as being a finder pattern"""
        width, height = self._image.width, self._image.height
        if fp.c1[0] <= 1 or fp.c1[1] <= 1:
            return False

        if fp.c1[0] >= width-2 or fp.c1[1] >= height-2:
            return False

        return True
