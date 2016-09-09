from .locate import Locator
from .read import DatamatrixReaderError, ReedSolomonError
from .read import DatamatrixBitReader
from .read import DatamatrixByteExtractor
from .read import ReedSolomonDecoder
from .read import DatamatrixByteInterpreter


# We predict the location of the center of each square (pixel/bit) in the datamatrix based on the
# size and location of the finder pattern, but this can sometimes be slightly off. If the initial
# reading doesn't produce sensible results, we try to offset the estimated location of the squares
# and try again.
wiggle_offsets = [[0, 0]]


class BarcodeReadNotPerformedException(Exception):
    pass


class BarcodeReadAlreadyPerformedException(Exception):
    pass


class DataMatrix:
    """ Representation of a DataMatrix and its location in an image.
    """
    DEFAULT_SIZE = 14
    DEFAULT_MESSAGE_LENGTH = 8

    _w = 0.25
    DIAG_WIGGLES = [[0, 0], [_w, _w], [-_w, -_w], [_w, -_w], [-_w, _w]]

    def __init__(self, finder_pattern, image):
        """ Initialize the DataMatrix object with its finder pattern location in an image. To actually
        interpret the DataMatrix, the perform_read() function must be called, which will attempt to read
        the DM from the supplied image.

        The matrix size is the width/height (in modules) of the Data matrix (including +2 for the edges).
        The message length is the number of data bytes in the encoded message (i.e. not including the
        error correction bytes).
        """
        self._finder_pattern = finder_pattern
        self._image = image.img
        self._matrix_size = self.DEFAULT_SIZE
        self._message_length = self.DEFAULT_MESSAGE_LENGTH

        self._data = None
        self._error_message = ""
        self._read_ok = False
        self._damaged_symbol = False
        self._is_read_performed = False

    def set_matrix_size(self, matrix_size):
        self._matrix_size = matrix_size

    def set_message_length(self, message_length):
        self._message_length = message_length

    def perform_read(self, offsets=wiggle_offsets, force_read=False):
        """ Attempt to read the DataMatrix from the image supplied in the constructor at the position
        given by the finder pattern. This is not performed automatically upon construction because the
        read operation is relatively expensive and might not always be needed.
        """
        if not self._is_read_performed or force_read:
            # Read the data contained in the barcode from the image
            self._read(self._image, offsets)
            self._is_read_performed = True

    def is_read(self):
        """ True if the read operation has been performed (whether successful or not) """
        return self._is_read_performed

    def is_valid(self):
        """ True if the data matrix was read successfully. """
        if not self._is_read_performed:
            raise BarcodeReadNotPerformedException()

        return self._read_ok

    def is_unreadable(self):
        """ True if the data matrix could not be decoded (because of damage to the symbol). """
        if not self._is_read_performed:
            raise BarcodeReadNotPerformedException()

        return self._damaged_symbol

    def data(self):
        """ String representation of the barcode data. """
        if not self._is_read_performed:
            raise BarcodeReadNotPerformedException()

        if self._read_ok:
            return self._data
        else:
            return ''

    def bounds(self):
        """ A circle which bounds the data matrix (center, radius). """
        return self._finder_pattern.bounds()

    def center(self):
        """ The center position (x,y) of the DataMatrix finder pattern. """
        return self._finder_pattern.center

    def radius(self):
        """ The radius (center-to-corner distance) of the DataMatrix finder pattern. """
        return self._finder_pattern.radius

    def _read(self, gray_image, offsets):
        """ From the supplied grayscale image, attempt to read the barcode at the location
        given by the datamatrix finder pattern.
        """
        bit_reader = DatamatrixBitReader(self._matrix_size)
        extractor = DatamatrixByteExtractor()
        decoder = ReedSolomonDecoder()
        interpreter = DatamatrixByteInterpreter()

        # Try a few different small offsets for the sample positions until we find one that works
        for offset in offsets:
            # Read the bit array at the target location (with offset)
            # If the bit array is valid, decode it and create a datamatrix object
            try:
                bit_array = bit_reader.read_bit_array(self._finder_pattern, offset, gray_image)
                encoded_bytes = extractor.extract_bytes(bit_array)
                decoded_bytes = decoder.decode(encoded_bytes, self._message_length)
                data = interpreter.interpret_bytes(decoded_bytes)

                self._data = data
                self._read_ok = True
                self._error_message = ""
                break
            except (DatamatrixReaderError, ReedSolomonError) as ex:
                self._read_ok = False
                self._error_message = str(ex)

        self._damaged_symbol = not self._read_ok

    def draw(self, img, color):
        """ Draw the lines of the finder pattern on the specified image. """
        fp = self._finder_pattern
        img.draw_line(fp.c1, fp.c2, color)
        img.draw_line(fp.c1, fp.c3, color)

    @staticmethod
    def locate_all_barcodes_in_image(grayscale_img):
        """ Searches the image for all datamatrix finder patterns
        """
        locator = Locator()
        finder_patterns = locator.locate_shallow(grayscale_img)
        unread_barcodes = [DataMatrix(fp, grayscale_img) for fp in finder_patterns]
        return list(unread_barcodes)

    @staticmethod
    def locate_all_barcodes_in_image_deep(grayscale_img):
        """ Searches the image for all datamatrix finder patterns
        """
        # TODO: deep scan is more likely to find some false finder patterns. Filter these out
        locator = Locator()
        locator.set_median_radius_tolerance(0.2)
        finder_patterns = locator.locate_deep(grayscale_img, expected_radius=None, filter_overlap=True)

        unread_barcodes = [DataMatrix(fp, grayscale_img) for fp in finder_patterns]
        return list(unread_barcodes)
