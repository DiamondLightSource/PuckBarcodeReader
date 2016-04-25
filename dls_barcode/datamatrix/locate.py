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
        self._single = False


    def locate_datamatrices(self, gray_img, single=False, expected_radius=0):

        self._image = gray_img
        self._single = single
        self._median_radius = expected_radius

        if single:
            finder_patterns = self._contours_single()
            finder_patterns = list(filter(self._filter_image_edges, finder_patterns))
            finder_patterns = list(filter(self._filter_median_radius, finder_patterns))
            if not finder_patterns:
                pass#finder_patterns = [self._square_single()]

        else:
            finder_patterns = self._contours_global()

            # Filter out any which differ significantly in size
            if len(finder_patterns) > 3:
                self._median_radius = np.median([fp.radius for fp in finder_patterns])
                finder_patterns = list(filter(self._filter_median_radius, finder_patterns))

        # check that finder patterns dont overlap
        valid_patterns = []
        for fp in finder_patterns:
            in_radius = False
            for ex in valid_patterns:
                in_radius = in_radius | ex.point_in_radius(fp.center)
            if not in_radius:
                valid_patterns.append(fp)

        return valid_patterns

    def _contours_global(self):
        C_values = [16,8]
        morphsize = 3
        blocksize = 35

        # Use a couple of different values of C as much more likely to locate the finder patterns
        finder_patterns = []
        for C in C_values:
            fps = ContourLocator().locate_datamatrices(self._image, blocksize, C, morphsize)
            finder_patterns.extend(fps)

        return finder_patterns

    def _contours_single(self):
        C_values = [0,4,20,16,8]
        morphsizes = [3,2]
        blocksize = 35

        # Use a couple of different values of C as much more likely to locate the finder patterns
        finder_patterns = []
        for ms in morphsizes:
            for C in C_values:
                fps = ContourLocator().locate_datamatrices(self._image, blocksize, C, ms)
                finder_patterns.extend(fps)

        return finder_patterns

    def _square_single(self):
        fp = SquareLocator().locate(self._image, self._median_radius)
        return fp

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
