from .locate import Locator
from .read import Reader
from .decode import Decoder
from .reedsolo import ReedSolomonError

# We predict the location of the center of each square (pixel/bit) in the datamatrix based on the
# size and location of the finder pattern, but this can sometimes be slightly off. If the initial
# reading doesn't produce sensible results, we try to offset the estimated location of the squares
# and try again.
wiggle_offsets = [[0,0]]

# Data value that is returned if the barcode cannot be read for whatever reason
BAD_DATA_SYMBOL = "-CANT-READ-"

class DataMatrix:
    def __init__(self, finder_pattern, gray_img, offsets=wiggle_offsets):
        """ Representation of a DataMatrix in an image.
        """
        self._finder_pattern = finder_pattern
        self._data = None
        self._error_message = ""
        self._read_ok = False
        self._damaged_symbol = False
        self._offsets = offsets

        # Read the data contained in the barcode from the image
        self._read(gray_img.img)

    def data(self):
        if self._read_ok:
            return self._data
        elif self._damaged_symbol:
            return BAD_DATA_SYMBOL
        else:
            return ''

    def bounds(self):
        """ A circle which bounds the data matrix (center, radius)
        """
        return self._finder_pattern.bounds()

    def is_valid(self):
        """ True if the data matrix was read successfully
        """
        return self._read_ok

    def is_unreadable(self):
        """ True if the data matrix could not be decoded (because of damage to the symbol)
        """
        return self._damaged_symbol

    def _read(self, gray_image):
        """ From the supplied grayscale image, attempt to read the barcode at the location
        given by the datamatrix finder pattern.
        """
        reader = Reader()
        decoder = Decoder()

        # Try a few different small offsets for the sample positions until we find one that works
        for offset in self._offsets:
            # Read the bit array at the target location (with offset)
            bit_array = reader.read_bitarray(self._finder_pattern, offset, gray_image)

            # If the bit array is valid, decode it and create a datamatrix object
            if bit_array is not None:
                # Decode the bits from the datamatrix
                try:
                    self._data = decoder.read_datamatrix(bit_array)
                    self._read_ok = True
                    self._damaged_symbol = False
                    self._error_message = ""
                    break
                except (ReedSolomonError, Exception) as ex:
                    self._read_ok = False
                    self._damaged_symbol = True
                    self._error_message = ex.message

    def draw(self, cvimg, ok_color, bad_color):
        """ Draw the lines of the finder pattern on the specified image
        """
        fp = self._finder_pattern
        color = bad_color if self.is_unreadable() else ok_color
        cvimg.draw_line(fp.c1, fp.c2, color)
        cvimg.draw_line(fp.c1, fp.c3, color)

    @staticmethod
    def LocateAllBarcodesInImage(grayscale_img):
        """ Searches the image for all datamatrix finder patterns
        """
        locator = Locator()
        finder_patterns = locator.locate_datamatrices(grayscale_img)
        return list(finder_patterns)