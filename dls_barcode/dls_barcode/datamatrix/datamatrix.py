from locate import Locator
from read import Reader
from decode import Decoder

# We predict the location of the center of each square (pixel/bit) in the datamatrix based on the
# size and location of the finder pattern, but this can sometimes be slightly off. If the initial
# reading doesn't produce sensible results, we try to offset the estimated location of the squares
# and try again.
w = 0.25
w2 = 0.5
wiggle_offsets = [[0,0],[w, w],[-w,-w],[w,-w],[-w,w],[w,0],[0,w],[-w,0],[0,-w],
                    [w2, w2],[-w2,-w2],[w2,-w2],[-w2,w2],[w2,0],[0,w2],[-w2,0],[0,-w2]]

BAD_DATA_SYMBOL = "XXXXXXXXXX"

# TODO: validation of the barcode based on a format, e.g. NNxxxNxxxx


class DataMatrix:
    def __init__(self):
        self._data = None
        self.bounds = None
        self.pinSlot = None
        self._finderPattern = None
        self._sampleLocations = None
        self._bitArray = None
        self._decodedBytes = None
        self._errorMessage = ""

        self._read_ok = False
        self._damaged_symbol = False

    def data(self):
        if self._read_ok:
            return self._data
        elif self._damaged_symbol:
            return BAD_DATA_SYMBOL
        else:
            return ''

    def is_valid(self):
        return self._read_ok

    def is_unreadable(self):
        return self._damaged_symbol

    def draw(self, cvimg, ok_color, bad_color):
        # draw circle and line highlights
        fp = self._finderPattern
        color = bad_color if self.is_unreadable() else ok_color
        cvimg.draw_line(fp.c1, fp.c2, color)
        cvimg.draw_line(fp.c1, fp.c3, color)
        cvimg.draw_text(text=str(self.pinSlot), position=fp.center, color=color, centered=True)
        for point in self._sampleLocations:
            cvimg.draw_dot(tuple(point), color, 1)

    @staticmethod
    def ReadAllBarcodesInImage(grayscale_img):
        """Searches a grayscale image for any data matricies that it can find, reads and decodes them
        and returns them as a list of DataMatrix objects
        """
        data_matricies = []
        puck = None

        # Create utility objects
        locator = Locator()
        reader = Reader()
        decoder = Decoder()

        # Find all the datamatrix locations in the image
        finder_patterns = locator.locate_datamatrices(grayscale_img)

        # Read the datamatricies
        for finder_pattern in finder_patterns:
            dm = DataMatrix()
            dm._finderPattern = finder_pattern
            dm.bounds = (finder_pattern.center, finder_pattern.radius)

            # Try a few different small offsets for the sample positions until we find one that works
            for offset in wiggle_offsets:

                # Read the bit array at the target location (with offset)
                bit_array, sample_points = reader.read_bitarray(finder_pattern, offset, grayscale_img)

                # If the bit array is valid, decode it and create a datamatrix object
                if bit_array is not None:
                    dm._bitArray = bit_array
                    dm._sampleLocations = sample_points

                    # Decode the bits from the datamatrix
                    try:
                        data, decoded_bytes = decoder.read_datamatrix(bit_array)
                        dm._data = data
                        dm._decodedBytes = decoded_bytes
                        dm._read_ok = True
                        dm._errorMessage = ""
                        break
                    except Exception as ex:
                        dm._errorMessage = ex.message
                        dm._data = BAD_DATA_SYMBOL
                        dm._damaged_symbol = True

            data_matricies.append(dm)

        return data_matricies