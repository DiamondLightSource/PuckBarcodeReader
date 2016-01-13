from locate import Locator
from read import Reader
from decode import Decoder

# We predict the location of the center of each square (pixel/bit) in the datamatrix based on the
# size and location of the finder pattern, but this can sometimes be slightly off. If the initial
# reading doesn't produce sensible results, we try to offset the estimated location of the squares
# and try again.
w = 0.25
wiggle_offsets = [[0,0],[w, w],[-w,-w],[w,-w],[-w,w]]

BAD_DATA_SYMBOL = "XXXXXXXXXX"

# TODO: validation of the barcode based on a format, e.g. NNxxxNxxxx


class DataMatrix:
    def __init__(self, finder_pattern):
        self._finder_pattern = finder_pattern

        self.pinSlot = None
        self._data = None
        self._error_message = ""

        self._read_ok = False
        self._damaged_symbol = False

    def data(self):
        if self._read_ok:
            return self._data
        elif self._damaged_symbol:
            return BAD_DATA_SYMBOL
        else:
            return ''

    def bounds(self):
        return self._finder_pattern.bounds()

    def is_valid(self):
        return self._read_ok

    def is_unreadable(self):
        return self._damaged_symbol

    def read(self, gray_image):
        """ From the supplied grayscale image, attempt to read the barcode at the location
        given by the datamatrix finder pattern.
        """
        reader = Reader()
        decoder = Decoder()

        # Try a few different small offsets for the sample positions until we find one that works
        for offset in wiggle_offsets:
            # Read the bit array at the target location (with offset)
            bit_array = reader.read_bitarray(self._finder_pattern, offset, gray_image)

            # If the bit array is valid, decode it and create a datamatrix object
            if bit_array is not None:
                # Decode the bits from the datamatrix
                try:
                    self._data = decoder.read_datamatrix(bit_array)
                    self._read_ok = True
                    self._error_message = ""
                    break
                except Exception as ex:
                    self._error_message = ex.message
                    self._data = BAD_DATA_SYMBOL
                    self._damaged_symbol = True

    def draw(self, cvimg, ok_color, bad_color):
        # draw circle and line highlights
        fp = self._finder_pattern
        color = bad_color if self.is_unreadable() else ok_color
        cvimg.draw_line(fp.c1, fp.c2, color)
        cvimg.draw_line(fp.c1, fp.c3, color)
        cvimg.draw_text(text=str(self.pinSlot), position=fp.center, color=color, centered=True)

    @staticmethod
    def ReadAllBarcodesInImage(grayscale_img):
        """Searches a grayscale image for any data matricies that it can find, reads and decodes them
        and returns them as a list of DataMatrix objects
        """
        data_matricies = []
        puck = None

        # Find all the datamatrix locations in the image
        locator = Locator()
        finder_patterns = locator.locate_datamatrices(grayscale_img)

        # Read the datamatricies
        for finder_pattern in finder_patterns:
            dm = DataMatrix(finder_pattern)
            dm.read(grayscale_img)
            data_matricies.append(dm)

        return data_matricies