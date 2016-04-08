import math

from dls_barcode.datamatrix import DataMatrix
from dls_barcode.util import Transform

# TODO: Write appropriate functions in the Scanner and ContinuousScan classes that uses Tray

# TODO: (possible) Allow for multiple unconnected networks of nodes that can be joined up later
# TODO:     when some common nodes are found in a subsequent image


class Tray:
    """ Represents a large tray containing many pins/barcodes with no particular geometry.
    The full representation of the tray is established by scanning a series of images, each
    of which contains some of the barcodes in the tray. When looking at the current frame
    (image), if we can find at least two barcodes that we have previously seen, we can
    correctly orient the new frame in relation to the existing set of known barcodes and so
    determine the relative positions of any new barcodes.

    This method allows us to scan a tray that contains many more pins than can reasonably fit
    into a single frame, by building up a composite image over time.
    """
    def __init__(self):
        self.nodes = []
        self.initialized = False

        # Per frame state
        self.last_frame = None
        self.frame_aligned = False
        self.frame_transform = None
        self.known_barcodes = []

    def new_frame(self, finder_patterns, image):
        """ Examine the new frame looking for barcodes and try to add any found into our
        existing representation.

        Note that locating all the barcodes in an image is relatively cheap but actually
        reading them is relatively expensive so we try to perform this operation with the
        minimum number of reads necessary, i.e. we dont want to re-read many barcodes that
        we have read in an earlier frame.

        Algorithm:
        * Read barcodes at random until we find two barcodes in the new set that we have
            already seen before.
        * Use the known positions of these two nodes to create a transformation that maps
            the set of points in the new frame onto the existing network of known barcode positions.
        * Transform the positions of the remaining unknown barcodes into the existing space.
        * Identify barcodes in the new list that have positions that match positions of barcodes
            already in the network - perform slight corrections to the positions of these.
        * Read any remaining unknown barcodes and add all new barcodes to the tray network.
        """
        # Store reference to last frame for user by clients
        self.last_frame = image

        # The tray is initialised once we have scanned at least 2 barcodes
        if len(self.nodes) < 2: self.nodes = []
        self.initialized = len(self.nodes) >= 2

        # Store finder patterns in a struct that can also store the associated barcode when
        # found. This allows us to easily keep track of which have been read already.
        barcode_searches = [BarcodeSearch(fp, None) for fp in finder_patterns]

        # Reset state that is relevant to the current frame only
        self.frame_aligned = False
        self.last_frame = None
        self.frame_transform = Transform(0,0,0,1)
        self.known_barcodes = []

        # Keep searching barcodes until we find two that we've seen before
        for search in barcode_searches:
            # Read the barcode
            self._read_barcode(search, image)

            # If its valid, check if we've seen it before, and attempt alignment
            if search.barcode.is_valid():
                self._register_barcode(search.barcode)

            # Stop searching if we've aligned the frame with the existing known barcodes
            if self.frame_aligned:
                break

        # If unable to align, do not proceed (unless we don't have any barcodes yet)
        if self.initialized and not self.frame_aligned:
            return None

        # Find all the barcodes and add them to the network if they are new. Since we
        # now have a mapping from the image space to our existing space, we can see if
        # any of the unread barcodes match the locations of barcodes we have read before.
        # If this is the case, we don't need to read them again as we already know what
        # they are.
        for search in barcode_searches:
            # Transform the barcode location in the new image into the existing coordinate system
            img_position = search.finder_pattern.center
            img_radius = search.finder_pattern.radius
            position = self.frame_transform.reverse(img_position)
            radius = img_radius / self.frame_transform.zoom

            # Check if we've seen a barcode at this location before
            if search.barcode is None:
                search.barcode = self._get_barcode_at_location(position)

            # If we haven't seen a barcode at this location before, read it
            if search.barcode is None:
                self._read_barcode(search, image)

            # If this is a new barcode, add it to the tray, else update its position
            barcode = search.barcode
            if barcode.is_valid() and not self.contains_node(barcode.data()):
                node = Node(barcode, position, radius)
                self.nodes.append(node)
            elif barcode.is_valid():
                self._update_node_position(barcode, position)

        return self.frame_transform


    @staticmethod
    def _read_barcode(barcode_search, image):
        """ Read the barcode located at the search's finder pattern. """
        fp = barcode_search.finder_pattern
        barcode_search.barcode = DataMatrix(fp, image)

    def _register_barcode(self, barcode):
        """ Check if the barcode has been seen before. If so, add it to the list of
        known barcodes (for ths frame), and attempt to perform an alignment if we've
        got 2 known barcodes.
        """
        if self.contains_node(barcode.data()):
            self.known_barcodes.append(barcode)

        if not self.frame_aligned and len(self.known_barcodes) >= 2:
            self._determine_mapping()

    def _determine_mapping(self):
        """ Using a known line in the existing network (i.e. positions of two barcodes)
        and the same line (positions of same two barcodes) in the new image, generate
        a transform that maps the former to the latter.
        """
        known1 = self.known_barcodes[0]
        known2 = self.known_barcodes[1]

        # Get coordinates of the existing barcodes
        A = self.get_node(known1.data()).position
        B = self.get_node(known2.data()).position
        A_ = known1.bounds()[0]
        B_ = known2.bounds()[0]

        self.frame_transform = Transform.line_mapping(A, B, A_, B_)
        self.frame_aligned = True

    def _get_barcode_at_location(self, point):
        """ Get the barcode that is at/near the specified location (or None). """
        for node in self.nodes:
            radius_sq = node.radius * node.radius
            if distance_sq(node.position, point) < radius_sq:
                print(math.sqrt(distance_sq(node.position, point)))
                return node.barcode
        return None

    def _update_node_position(self, barcode, position):
        """ Update the position of an existing node. """
        node = self.get_node(barcode.data())
        node.position = position

    def get_node(self, data):
        """ Get the node (barcode) with the specified data or return None. """
        for node in self.nodes:
            if node.valid() and node.data() == data:
                return node

        return None

    def contains_node(self, data):
        """ True if the tray contains a node with the specified barcode date. """
        known_data = [n.data() for n in self.nodes]
        return data in known_data

    def draw_highlights(self, cvimg, color):
        """ Draws an outline of each bacrcode location on the supplied image. """
        for node in self.nodes:
            center = self.frame_transform.transform(node.position)
            radius = node.radius * self.frame_transform.zoom

            cvimg.draw_dot(center, color)
            cvimg.draw_circle(center, radius, color)


class Node:
    """ Represents a single barcode and its position in the tray network.
    """
    def __init__(self, barcode, position, radius):
        self.barcode = barcode
        self.position = position
        self.radius = radius * 1.5

    def valid(self):
        return self.barcode.is_valid()

    def data(self):
        return self.barcode.data()


class BarcodeSearch:
    """ Struct that contains a data matrix finder pattern and the associated
    barcode (if it has been read)"""
    def __init__(self, finder_pattern, barcode):
        self.finder_pattern = finder_pattern
        self.barcode = barcode


def distance_sq(a, b):
    """ Calculates the square of the distance from a to b.
    """
    x = a[0]-b[0]
    y = a[1]-b[1]
    return x**2+y**2



