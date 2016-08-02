from .locate import Locator
from .read import Reader
from .decode import Decoder
from .reedsolo import ReedSolomonError

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
    def __init__(self, finder_pattern, image):
        """ Initialize the DataMatrix object with its finder pattern location in an image. To actually
        interpret the DataMatrix, the perform_read() function must be called, which will attempt to read
        the DM from the supplied image."""
        self._finder_pattern = finder_pattern
        self._image = image.img
        self._data = None
        self._error_message = ""
        self._read_ok = False
        self._damaged_symbol = False
        self._is_read_performed = False

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
        reader = Reader()
        decoder = Decoder()

        # Try a few different small offsets for the sample positions until we find one that works
        for offset in offsets:
            # Read the bit array at the target location (with offset)
            bit_array = reader.read_bitarray(self._finder_pattern, offset, gray_image)

            # Todo: empty detection?
            if bit_array is None:
                continue

            # If the bit array is valid, decode it and create a datamatrix object
            try:
                self._data = decoder.read_datamatrix(bit_array)
                self._read_ok = True
                self._error_message = ""
                break
            except (ReedSolomonError, Exception) as ex:
                self._read_ok = False
                self._error_message = ex.message

        self._damaged_symbol = not self._read_ok

    def draw(self, cvimg, color):
        """ Draw the lines of the finder pattern on the specified image. """
        fp = self._finder_pattern
        cvimg.draw_line(fp.c1, fp.c2, color)
        cvimg.draw_line(fp.c1, fp.c3, color)

    @staticmethod
    def LocateAllBarcodesInImage(grayscale_img):
        """ Searches the image for all datamatrix finder patterns
        """
        locator = Locator()
        finder_patterns = locator.locate_shallow(grayscale_img)
        unread_barcodes = [DataMatrix(fp, grayscale_img) for fp in finder_patterns]
        return list(unread_barcodes)
