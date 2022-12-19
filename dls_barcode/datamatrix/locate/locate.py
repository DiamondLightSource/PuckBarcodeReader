from __future__ import division

import math

import numpy as np

from .locate_contour import ContourLocator


class Locator:
    """ Provides access to several different algorithms for locating (not reading) datamatrix
    finder patterns in an image.
    """
    def __init__(self):
        self._median_radius_tolerance = 0.3
        self._median_radius = 0
        self._image = None

    def set_median_radius_tolerance(self, value):
        """ The contour methods filter their results by eliminating any supposed finder patterns that differ
        in size significantly from the median size of located finder patterns in the image. The tolerance
        defines how much the size of a pattern must differ by before it is discarded. """
        self._median_radius_tolerance = value

    def locate_shallow(self, img):
        """ Use contour locating algorithm to locate finder patterns in the image. Uses a single set of
        parameters to the contour algorithm. This is quick to run and most suitable for scanning an image
        that contains multiple datamatrices. To run the algorithm multiple times with varying parameters,
        use locate_deep(). """
        # Locate finder patterns in whole image
        finder_patterns = self._contours_shallow(img)

        # Filter out any which differ significantly in size
        if len(finder_patterns) > 3:
            self._median_radius = np.median([fp.radius for fp in finder_patterns])
            finder_patterns = list(filter(self._filter_median_radius, finder_patterns))

        valid_patterns = self._filter_overlapping_patterns(finder_patterns)

        return valid_patterns

    def locate_deep(self, img, expected_radius=None, filter_overlap=False):
        """ Use contour locating algorithm to locate finder patterns in the image. Runs the algorithm
        multiple times with different sets of parameters and combines the results. This can be used to
        locate multiple datamatrices in a large image, but can also be used to locate a single one in a
        small image if locate_shallow() was unable to do so.

        Finder patterns which differ in size significantly from the supplied expected radius will be
        discarded. If no value is supplied, one will calculated automatically.

        Each run of the algorithm is likely to locate a given datamatrix, so there may be multiple finder
        patterns that correspond to the same datamatrix, each of which may be position slightly differently.
        If filter_overlap is True, any pattern that overlaps an existing one will be discarded. Leaving this
        filter off and attempting to read all of the finder patterns is therefore more likely to produce a
        valid result, but will of course be more computationally expensive.
        """
        self._median_radius = expected_radius
        self._image = img

        finder_patterns = self._contours_deep(img)

        if expected_radius is None and any(finder_patterns):
            expected_radius = np.median([fp.radius for fp in finder_patterns])

        self._median_radius = expected_radius

        finder_patterns = list(filter(self._filter_image_edges, finder_patterns))
        finder_patterns = list(filter(self._filter_median_radius, finder_patterns))

        if filter_overlap:
            finder_patterns = self._filter_overlapping_patterns(finder_patterns)

        # If the fps are asymmetrical, correct the side lengths
        if expected_radius is not None:
            side = expected_radius * (2 / math.sqrt(2))
            finder_patterns = [fp.correct_lengths(side) for fp in finder_patterns]

        return finder_patterns

    @staticmethod
    def _contours_shallow(img):
        """ Run the contour locating algorithm with a single parameter set. """
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
        """ Run the contour locating algorithm multiple times with different parameter sets. """
        c_values = [16, 8, 0, 4, 20]
        morph_sizes = [3, 2]
        block_size = 35

        # Use a couple of different values of C as much more likely to locate the finder patterns
        finder_patterns = []
        for ms in morph_sizes:
            for C in c_values:
                fps = ContourLocator().locate_datamatrices(img, block_size, C, ms)
                finder_patterns.extend(fps)

        return finder_patterns

    @staticmethod
    def _filter_overlapping_patterns(finder_patterns):
        """ Filter out any finder patterns that overlap with others that appear earlier in the list. """
        # Filter out patterns that overlap
        valid_patterns = []
        for fp in finder_patterns:
            in_radius = False
            for ex in valid_patterns:
                in_radius = in_radius | ex.point_in_radius(fp.center)
            if not in_radius:
                valid_patterns.append(fp)
        return valid_patterns

    def _filter_median_radius(self, fp):
        """Return true iff finder pattern radius is close to the median"""
        median = self._median_radius
        tolerance = self._median_radius_tolerance * median
        return (median - tolerance) < fp.radius < (median + tolerance)

    def _filter_image_edges(self, fp):
        """Return true if the finder pattern isn't right along on of the edges of the image.
        This is needed because the algorithm sometimes detects the edge of the image as being a finder pattern"""
        width, height = self._image.width, self._image.height
        if fp.c1.x <= 1 or fp.c1.y <= 1:
            return False

        if fp.c1.x >= width-2 or fp.c1.y >= height-2:
            return False

        return True
