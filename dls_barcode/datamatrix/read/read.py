from __future__ import division

import numpy as np
import itertools

from .exception import DatamatrixReaderError


class DatamatrixReader:
    """ Contains functionality to read the bit pattern that encodes a barcode from an image
    """

    def __init__(self, matrix_size):
        self._matrix_size = matrix_size

    def read_bitarray(self, finder_pattern, offset, cv_img):
        """ Return a datamatrix boolean array by sampling points in the image array.

        After extracting the samples, this function performs a threshold on each ([0, 255] -> [0, 1])
        based on what it perceives as the optimal threshold value. To find this optimum, it gets the
        minimal and maximal threshold values which result in valid datamatrices, and bisects the two.
        Or, if that doesn't work, it uses a threshold value for which the result looks most plausibly
        like a datamatrix (i.e. fewest border defects). In this case, maybe Reed-Solomon can get us
        out of a hole.

        If this function doesn't work, it's quite likely that the cause is that one of the vectors
        passed in has slightly the wrong length.
        """
        n = self._matrix_size

        try:
            # Determine the pixel locations to sample
            datamatrix_samples = np.empty((n, n))
            grid = self._datamatrix_sample_points(finder_pattern, offset, matrix_size=n)
            for ((x, y), point) in grid:
                datamatrix_samples[y, x] = int(self._window_average(cv_img, point))

            thresholds = [self._threshold(datamatrix_samples, val) for val in range(256)]
            b_errors = [self._border_errors(t) for t in thresholds]
            best_threshold_value, badness = self._smart_minimum(b_errors)

            _ = badness  # Throw this away (for now).
            # TODO: Tweak vector lengths to minimise badness?

            # Flip the datamatrix so its reference corner is at large i, small j.
            # Also now remove the border (reference edges and timing patterns).
            bit_array = self._threshold(datamatrix_samples, best_threshold_value)[::-1, :][1:-1, 1:-1]

        except IndexError:
            raise DatamatrixReaderError("Error reading Datamatrix")

        self._perform_sanity_check(bit_array)

        return bit_array

    @staticmethod
    def _datamatrix_sample_points(finder_pattern, offset, matrix_size):
        """ Get pixel positions corresponding to individual bits in a datamatrix. This is done based on the
        position of a datamatrix.

        Each returned pixel position comes also with an (x, y) pair which denotes the position of the
        corresponding bit in the datamatrix, starting at (0, 0) in the bottom left corner and up to (n-1, n-1)
        at the top right.

        The base and side vectors are free to be non-orthogonal, so any skew of the datamatrix (because of lens
        distortion, say) is already accounted for (to first order).
        """
        n = matrix_size
        corner = finder_pattern.corner.tuple()
        base_vec = np.asarray(finder_pattern.baseVector.tuple())
        side_vec = np.asarray(finder_pattern.sideVector.tuple())

        return (((x, y),
                 list(map(int, corner + ((2*x+1+offset[0])*base_vec + (2*y+1+offset[1])*side_vec)/(2*n))))
                for x, y in itertools.product(range(n), range(n)))

    @staticmethod
    def _smart_minimum(data):
        """Return the index half-way between the outermost minimising indices.

        To illustrate:
                    ...                 ..  ..
         ^data         ...            ..  ..
         |                ..    .. ...
         |   index          ....  .
         +--->              <--|-->

        The returned index is at the position of the pipe.
        """
        least_y = min(data)
        leftmost = data.index(least_y)
        rightmost = len(data) - list(reversed(data)).index(least_y)
        return int((leftmost + rightmost)/2), least_y

    @staticmethod
    def _window_average(arr, point, side=3):
        """Return the average brightness over a small region surrounding a point.
        """
        x1, y1 = point[0] - (side // 2), point[1] - (side // 2)
        x2, y2 = x1 + side, y1 + side
        brightness = int(np.sum(arr[y1:y2, x1:x2]) / (side * side))
        return brightness

    @staticmethod
    def _threshold(matrix, value):
        """Return a thresholded matrix, with low values corresponding to True.
        """
        value_matrix = np.empty_like(matrix)
        value_matrix.fill(value)
        return matrix < value_matrix

    @staticmethod
    def _border_errors(datamatrix_candidate):
        """Return the number of border bits not matching datamatrix specification.
        """
        n, m = datamatrix_candidate.shape
        # Could extend to non-square datamatrices (which do exist)...
        assert n == m and n % 2 == 0
        errors_in_base = datamatrix_candidate[:1, :] != np.ones((1, n))
        errors_in_side = datamatrix_candidate[:, :1] != np.ones((n, 1))
        errors_in_timing = (  # ("Timing pattern".)
            [[datamatrix_candidate[i, -1:]] != [(i+1) % 2] for i in range(n)] +
            [[datamatrix_candidate[-1:, i]] != [(i+1) % 2] for i in range(n)])
        return sum(map(np.sum, (errors_in_base, errors_in_side, errors_in_timing)))

    @staticmethod
    def _perform_sanity_check(bit_array):
        """ Do some simple checks on the array of datamatrix bits to make sure that it looks
        sensible. This weeds out any patterns that are obviously not datamatricies.
        """
        width = len(bit_array)
        height = len(bit_array[0])
        num_bits = width * height
        true_bits = 0

        for row in bit_array:
            true_bits = true_bits + sum(bool(x) for x in row)

        # We assume that if almost all of the bits are True or False then its not likely to be a valid datamatrix
        too_dark = true_bits > 0.9 * num_bits
        too_light = true_bits < 0.1 * num_bits

        if too_dark or too_light:
            raise DatamatrixReaderError("Area doesn't look like a Datamatrix (too many/too few bits)")
