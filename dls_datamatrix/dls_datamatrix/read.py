import numpy as np
import itertools

DEFAULT_MATRIX_SIZE = 14

class Reader():
    """Class for reading an array of bits at a specified location
    """

    def read_bitarray(self, finder_pattern, offset, cv_img, n=DEFAULT_MATRIX_SIZE):
        """Return a datamatrix boolean array by sampling points in the image array.

        After extracting the samples, this function performs a threshold on each
        ([0, 255] -> [0, 1]) based on what it perceives as the optimal threshold
        value. To find this optimum, it gets the minimal and maximal threshold
        values which result in valid datamatrices, and bisects the two. Or, if that
        doesn't work, it uses a threshold value for which the result looks most
        plausibly like a datamatrix (i.e. fewest border defects). In this case,
        maybe Reed-Solomon can get us out of a hole.

        This method was chosen because, despite its simplicity, it seems to work
        quite well, and doesn't involve handing off a region of interest to a black
        box datamatrix library. (libdmtx, accessible via pydmtx, is rather
        temperamental. Interfacing to zxing, a Java library, seems like a
        challenge.)

        If this function doesn't work, it's quite likely that the cause is that one
        of the vectors passed in has slightly the wrong length.
        """

        # Determine the pixel locations to sample
        datamatrix_samples = np.empty((n, n))
        sample_points = []
        grid = self._datamatrix_sample_points(*finder_pattern.pack(), offset=offset, n=n)
        for ((x, y), point) in grid:
            datamatrix_samples[y, x] = int(self._window_average(cv_img, point))
            sample_points.append(point)


        thresholds = [self._threshold(datamatrix_samples, val) for val in range(256)]
        b_errors = [self._border_errors(t) for t in thresholds]
        best_threshold_value, badness = self._smart_minimum(b_errors)

        _ = badness  # Throw this away (for now).
        # TODO: Tweak vector lengths to minimise badness?

        # Flip the datamatrix so its reference corner is at large i, small j.
        # Also now remove the border (reference edges and timing patterns).
        bitArray = self._threshold(datamatrix_samples, best_threshold_value)[::-1, :][1:-1, 1:-1]

        if self._sanity_check(bitArray):
            return bitArray, sample_points
        else:
            return None, sample_points

    def _smart_minimum(self, data):
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

    def _datamatrix_sample_points(self, corner, base_vec, side_vec, offset, n=DEFAULT_MATRIX_SIZE):
        """Get pixel positions corresponding to individual bits in a datamatrix.

        This is done based on the position of a datamatrix, passed in as a
        splatted "reference corner" tuple.

        Each returned pixel position comes also with an (x, y) pair which denotes
        the position of the corresponding bit in the datamatrix, starting at (0, 0)
        in the bottom left corner and up to (n-1, n-1) at the top right.

        The base and side vectors are free to be non-orthogonal, so any skew of the
        datamatrix (because of lens distortion, say) is already accounted for (to
        first order).
        """
        return (((x, y),
                 map(int, corner + ((2*x+1+offset[0])*(base_vec) + (2*y+1+offset[1])*side_vec)/(2*n)))
                    for x, y in itertools.product(range(n), range(n)))

    def _window_average(self, arr, point, side_length=3):
        """Return the average brightness over a small region surrounding a point.
        """
        sum = 0
        for i, j in itertools.product(
                range(-(side_length//2), (side_length//2)+1),
                range(-(side_length//2), (side_length//2)+1)):
            sum += arr[point[1] + i, point[0] + j]
        return int(sum/(side_length*side_length))

    def _threshold(self, matrix, value):
        """Return a thresholded matrix, with low values corresponding to True.
        """
        value_matrix = np.empty_like(matrix)
        value_matrix.fill(value)
        return matrix < value_matrix


    def _border_errors(self, datamatrix_candidate):
        """Return the number of border bits not matching datamatrix specification.
        """
        n, m = datamatrix_candidate.shape
        # Could extend to non-square datamatrices (which do exist)...
        assert n == m and n % 2 == 0
        errors_in_base = datamatrix_candidate[:1, :] != np.ones((1, n))
        errors_in_side = datamatrix_candidate[:, :1] != np.ones((n, 1))
        errors_in_timing = (  # ("Timing pattern".)
            [[datamatrix_candidate[i, -1:]] != [(i+1) % 2] for i in range(n)]
            + [[datamatrix_candidate[-1:, i]] != [(i+1) % 2] for i in range(n)])
        return sum(map(np.sum, (errors_in_base, errors_in_side, errors_in_timing)))

    def _sanity_check(self, bitArray):
        """Do some simple checks on the array of datamatrix bits
        to make sure that it looks sensible. This weeds out any patterns
        that are obviously not datamatricies"""
        width = len(bitArray)
        height = len(bitArray[0])
        num_bits = width * height
        true_bits = 0
        for row in bitArray:
            true_bits = true_bits + sum(bool(x) for x in row)

        # We assume that if almost all of the bits are True or False then its not likely to be a valid barcode
        return true_bits < 0.9 * num_bits and true_bits > 0.1 * num_bits
