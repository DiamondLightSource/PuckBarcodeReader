from __future__ import division

import numpy as np
from functools import partial

from .locate_square import SquareLocator
from .locate_contour import ContourLocator


class Locator:

    def __init__(self):
        # Assume that all datamatricies are roughly the same
        #   size so filter out any obviously mis-sized ones
        self._median_radius_tolerance = 0.3
        self._median_radius = 0
        self._image = None


    def locate_datamatrices(self, gray_img, single=False, expected_radius=0):
        self._image = gray_img
        contour = ContourLocator()

        blocksize = 35

        if single:
            C_values = [0,4,20,16,8]
            morphsizes = [3,2]
            self._median_radius = expected_radius
        else:
            C_values = [16,8]
            morphsizes = [3]

        finder_patterns = []

        # Use a couple of different values of C as much more likely to locate the finder patterns
        for ms in morphsizes:
            for C in C_values:
                fps = contour.locate_datamatrices(gray_img.img, blocksize, C, ms)

                # If searching for barcodes on a single slot image, filter based on the supplied mean radius
                if single:
                    fps = filter(self._filter_image_edges, fps)
                    fps = filter(self._filter_median_radius, fps)

                # check that this doesnt overlap with any previous finder patterns
                for fp in fps:
                    in_radius = False
                    for ex in finder_patterns:
                        in_radius = in_radius | ex.point_in_radius(fp.center)
                    if not in_radius:
                        finder_patterns.append(fp)

        # Filter out any which differ significantly in size
        if len(finder_patterns) > 3:
            self._median_radius = np.median([fp.radius for fp in finder_patterns])
            finder_patterns = filter(self._filter_median_radius, finder_patterns)

        return finder_patterns

    def _filter_median_radius(self, fp):
        """Return true iff finder pattern radius is close to the median"""
        median = self._median_radius
        tolerance = self._median_radius_tolerance * median
        return (median - tolerance) < fp.radius < (median + tolerance)

    def _filter_image_edges(self, fp):
        """Return true if the finder pattern isnt right along on of the edges of the image.
        This is needed because the algorithm sometimes detects the edge of the image as being a finder pattern"""
        width, height = self._image.width, self._image.height
        if fp.c1[0] <= 1 or fp.c1[1] <= 1:
            return False

        if fp.c1[0] >= width-2 or fp.c1[1] >= height-2:
            return False

        return True