import math
from functools import partial, reduce
from operator import add

import cv2
import numpy as np

from dls_barcode.datamatrix.finder_pattern import FinderPattern
from dls_util.shape import Point
from dls_util.image import Image

OPENCV_MAJOR = cv2.__version__[0]


class ContourLocator:
    """ Utility for finding the positions of all of the datamatrix barcodes
    in an image """

    def __init__(self):
        pass

    def locate_datamatrices(self, gray_image, blocksize, C, close_size):
        """Get the positions of (hopefully all) datamatrices within an image.
        """
        # Perform adaptive threshold, reducing to a binary image
        threshold_image = self._do_threshold(gray_image, blocksize, C)

        # Perform a morphological close, removing noise and closing some gaps
        morphed_image = self._do_close_morph(threshold_image, close_size)

        # Find a bunch of contours in the image.
        contours = self._get_contours(morphed_image)
        polygons = self._contours_to_polygons(contours)

        # Convert lists of vertices to lists of edges (easier to work with).
        edge_sets = map(self._polygons_to_edges, polygons)

        # Discard all edge sets which probably aren't datamatrix perimeters.
        edge_sets = filter(self._filter_non_trivial, edge_sets)
        edge_sets = filter(self._filter_longest_adjacent, edge_sets)
        edge_sets = filter(self._filter_longest_approx_orthogonal, edge_sets)
        edge_sets = filter(self._filter_longest_similar_in_length, edge_sets)

        # Convert edge sets to FinderPattern objects
        fps = [self._get_finder_pattern(es) for es in edge_sets]

        return fps

    @staticmethod
    def _do_threshold(gray_image, block_size, c):
        """ Perform an adaptive threshold operation on the image. """
        raw = gray_image.img
        thresh = cv2.adaptiveThreshold(raw, 255.0, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c)
        return Image(thresh)

    @staticmethod
    def _do_close_morph(threshold_image, morph_size):
        """ Perform a generic morphological operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(threshold_image.img, cv2.MORPH_CLOSE, element, iterations=1)
        return Image(closed)

    @staticmethod
    def _get_contours(binary_image):
        """ Find contours and return them as lists of vertices. """
        raw_img = binary_image.img.copy()
        raw_contours, _ = cv2.findContours(raw_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        return raw_contours

    @staticmethod
    def _contours_to_polygons(contours, epsilon=6.0):
        """ Uses the Douglas-Peucker algorithm to approximate a polygon as a similar polygon with
        fewer vertices, i.e., it smooths the edges of the shape out. Epsilon is the maximum distance
        from the contour to the approximated contour; it controls how much smoothing is applied.
        A lower epsilon will mean less smoothing. """
        shapes = [cv2.approxPolyDP(rc, epsilon, True).reshape(-1, 2) for rc in contours]
        return shapes

    @staticmethod
    def _polygons_to_edges(vertex_list):
        """Return a list of edges based on the given list of vertices. """
        return list(ContourLocator._pairs_circular(vertex_list))

    @staticmethod
    def _pairs_circular(iterable):
        """ Generate pairs from an iterable. Best illustrated by example:

        >>> list(pairs_circular('abcd'))
        [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')]
        """
        iterator = iter(iterable)
        x = next(iterator)
        zeroth = x  # Keep the first element so we can wrap around at the end.
        while True:
            try:
                y = next(iterator)
                yield((x, y))
            except StopIteration:  # Iterator is exhausted so wrap around to start.
                try:
                    yield((y, zeroth))
                except UnboundLocalError:  # Iterable has one element. No pairs.
                    pass
                break
            x = y

    @staticmethod
    def _filter_non_trivial(edge_set):
        """Return True iff the number of edges is non-small.
        """
        return len(edge_set) > 6

    @staticmethod
    def _filter_longest_adjacent(edges):
        """Return True iff the two longest edges are adjacent.
        """
        i, j = ContourLocator._longest_pair_indices(edges)
        return abs(i - j) in (1, len(edges) - 1)

    @staticmethod
    def _filter_longest_approx_orthogonal(edges):
        """Return True iff the two longest edges are approximately orthogonal.
        """
        i, j = ContourLocator._longest_pair_indices(edges)
        v_i, v_j = (np.subtract(*edges[x]) for x in (i, j))
        return abs(_cosine(v_i, v_j)) < 0.1

    @staticmethod
    def _filter_longest_similar_in_length(edges):
        """Return True iff the two longest edges are similar in length.
        """
        i, j = ContourLocator._longest_pair_indices(edges)
        l_i, l_j = (_length(edges[x]) for x in (i, j))
        return abs(l_i - l_j)/abs(l_i + l_j) < 0.1

    @staticmethod
    def _longest_pair_indices(edges):
        """Return the indices of the two longest edges in a list of edges.
        """
        lengths = list(map(_length, edges))
        return np.asarray(lengths).argsort()[-2:][::-1]

    @staticmethod
    def _get_finder_pattern(edges):
        """Return information about the "main" corner from a set of edges.

        This function finds the corner between the longest two edges, which should
        be spatially adjacent (it is up to the caller to make sure of this). It
        returns the position of the corner, and vectors corresponding to the said
        two edges, pointing away from the corner. These two vectors are returned in
        an order such that their cross product is positive, i.e. (see diagram) the
        base vector (a) comes before the side vector (b).

              ^side
              |
              |   base
              X--->
         corner

        This provides a convenient way to refer to the position of a datamatrix.
        """
        self = ContourLocator

        i, j = self._longest_pair_indices(edges)
        pair_longest_edges = [edges[x] for x in (i, j)]
        x_corner = self._get_shared_vertex(*pair_longest_edges)
        c, d = map(partial(self._get_other_vertex, x_corner), pair_longest_edges)
        vec_c, vec_d = map(partial(np.add, -x_corner), (c, d))

        # FIXME: There seems to be a sign error here...
        if vec_c[0]*vec_d[1] - vec_c[1]*vec_d[0] < 0:
            vec_base, vec_side = vec_c, vec_d
        else:
            vec_base, vec_side = vec_d, vec_c

        x_corner = Point(x_corner[0], x_corner[1]).intify()
        vec_base = Point(vec_base[0], vec_base[1]).intify()
        vec_side = Point(vec_side[0], vec_side[1]).intify()
        return FinderPattern(x_corner, vec_base, vec_side)

    @staticmethod
    def _get_shared_vertex(edge_a, edge_b):
        """Return a vertex shared by two edges, if any.
        """
        for vertex_a in edge_a:
            for vertex_b in edge_b:
                if (vertex_a == vertex_b).all():
                    return vertex_a

    @staticmethod
    def _get_other_vertex(vertex, edge):
        """Return an element of `edge` which does not equal `vertex`.
        """
        for vertex_a in edge:
            if not (vertex_a == vertex).all():
                return vertex_a


def _length(edge):
    return _distance(*edge)


def _distance(point_a, point_b):
    return _modulus(np.subtract(point_a, point_b))


def _modulus(vector):
    return quadrature_add(*vector)


def _cosine(vec_a, vec_b):
    return np.dot(vec_a, vec_b)/(_modulus(vec_a) * _modulus(vec_b))


def quadrature_add(*values):
    return math.sqrt(reduce(add, (c*c for c in values)))