from locate import Locator
from read import Reader
from decode import Decoder

w = 0.25
w2 = 0.5
wiggle_offsets = [[0,0],[w, w],[-w,-w],[w,-w],[-w,w],[w,0],[0,w],[-w,0],[0,-w],
                    [w2, w2],[-w2,-w2],[w2,-w2],[-w2,w2],[w2,0],[0,w2],[-w2,0],[0,-w2]]


class DataMatrix:
    def __init__(self):
        self.pinSlot = None
        self.finderPattern = None
        self.sampleLocations = None
        self.bitArray = None
        self.decodedBytes = None
        self.data = None
        self.errorMessage = ""

    @staticmethod
    def ReadAllBarcodesInImage(grayscale_img):
        """Searches a grayscale image for any data matricies that it can find, reads and decodes them
        and returns them as a list of DataMatrix objects
        """

        # Result objects
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
            dm.finderPattern = finder_pattern

            # Try a few different small offsets for the sample positions until we find one that works
            for offset in wiggle_offsets:

                # Read the bit array at the target location (with offset)
                bit_array, sample_points = reader.read_bitarray(finder_pattern, offset, grayscale_img)

                # If the bit array is valid, decode it and create a datamatrix object
                if bit_array is not None:
                    dm.bitArray = bit_array
                    dm.sampleLocations = sample_points

                    # Decode the bits from the datamatrix
                    try:
                        data, decoded_bytes = decoder.read_datamatrix(bit_array)
                        dm.data = data
                        dm.decodedBytes = decoded_bytes
                        dm.errorMessage = ""
                        break
                    except Exception as ex:
                        dm.errorMessage = ex.message

            data_matricies.append(dm)

        return data_matricies