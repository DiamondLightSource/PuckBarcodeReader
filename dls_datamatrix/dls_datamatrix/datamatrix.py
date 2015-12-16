"""Takes an OpenCV image and attempts to read any Datamatrix barcodes in it.

As it is currently set up, all of this code assumes that we are trying to locate
an ECC 200 type datamatrix, which uses Reed-Solomon encoding. The DM is also
assumed to be 14x14, with a 12x12 data area, for a total of 18 bytes. It is
further assumed that 8 bytes are used for encoding data (including the EOM
byte) and the remaining 10 bytes are used for error-correction coding.

See: 'https://en.wikipedia.org/wiki/Data_Matrix' for more details about Data
Matrix

This depends on the following classes:
* Locator (locate.py) - scans the image for datamatrix finder patterns, which give
    the position and orientation of a datamatrix
* Reader (read.py) - looks at the location indicated by a finder pattern and attempts
    to read a bit array located there
* Decoder (decode.py) - interprets the bit array, reproducing the original message
    encoded in the data matrix. Uses Reed-Solomon error correction.
* Aligner (align.py) - aligns a virtual representation of the puck with the image,
    so that the slot number of each puin can be determined.

"""
import sys
if sys.version_info[0] < 3:
    from __future__ import division

from pkg_resources import require;  require('numpy')

from locate import Locator
from read import Reader
from decode import Decoder
from align import Aligner

"""
todo: New locator algorithm idea:

1. look at light vs dark areas to find roughly where the puck is
2. Crop the image to a rough square around the puck
3. predict pin radius and do circle detection
4. Draw square around each pin and perform barcode detection on it

"""


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
    def ScanImage(cvimg):
        """Searches the image for all Data Matrix, reads and decodes them
        and returns them as a list of DataMatrix objects
        """

        # Get a grayscale version of the image (easier to work with).
        grayscale_img = cvimg.to_grayscale().img

        # Result objects
        data_matricies = []
        puck = None

        # Create utility objects
        locator = Locator()
        reader = Reader()
        decoder = Decoder()
        aligner = Aligner()

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

                    # Decode the bits from the barcode
                    try:
                        data, decoded_bytes = decoder.read_datamatrix(bit_array)
                        dm.data = data
                        dm.decodedBytes = decoded_bytes
                        dm.errorMessage = ""
                        break
                    except Exception as ex:
                        dm.errorMessage = ex.message

            data_matricies.append(dm)

        # Align puck model with the image
        puck = aligner.get_puck_alignment(grayscale_img, finder_patterns)

        # Get sample pin slot numbers
        for dm in data_matricies:
            dm.pinSlot = aligner.get_slot_number(puck, dm.finderPattern)

        # Sort barcodes by slot number
        data_matricies = sorted(data_matricies, key=lambda dm: dm.pinSlot)


        return data_matricies, puck
