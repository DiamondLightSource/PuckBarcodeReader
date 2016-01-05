"""Takes an OpenCV image and attempts to read any Datamatrix barcodes in it.

As it is currently set up, all of this code assumes that we are trying to locate
an ECC 200 type datamatrix, which uses Reed-Solomon encoding. The DM is also
assumed to be 14x14, with a 12x12 data area, for a total of 18 bytes. It is
further assumed that 8 bytes are used for encoding data (including the EOM
byte) and the remaining 10 bytes are used for error-correction coding.

See: 'https://en.wikipedia.org/wiki/Data_Matrix' for more details about Data
Matrix
"""
from __future__ import division

from pkg_resources import require;  require('numpy')

from datamatrix.datamatrix import DataMatrix
from plate.align import Aligner

"""
todo: New locator algorithm idea:

1. look at light vs dark areas to find roughly where the puck is
2. Crop the image to a rough square around the puck
3. predict pin radius and do circle detection
4. Draw square around each pin and perform datamatrix detection on it

"""


class Scan:
    @staticmethod
    def ScanImage(cvimg):
        """Searches the image for all Data Matrix, reads and decodes them
        and returns them as a list of DataMatrix objects
        """

        # Get a grayscale version of the image (easier to work with).
        grayscale_img = cvimg.to_grayscale().img

        # Locate and read all the barcodes (data matricies) in the image
        barcodes = DataMatrix.ReadAllBarcodesInImage(grayscale_img)

        # Align plate (sample holder) model with the image
        aligner = Aligner()
        plate = aligner.get_plate(grayscale_img, barcodes)

        # Get sample pin slot numbers
        for bc in barcodes:
            center = bc.bounds[0]
            bc.pinSlot = aligner.get_slot_number(plate, center)

        # Sort barcodes by slot number
        barcodes = sorted(barcodes, key=lambda bc: bc.pinSlot)

        return barcodes, plate