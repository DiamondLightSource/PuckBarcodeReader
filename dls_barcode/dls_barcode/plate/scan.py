from __future__ import division
from dls_barcode.image import CvImage
from dls_barcode.datamatrix import DataMatrix
from unipuck import Unipuck
from plate import Plate

from pkg_resources import require;  require('numpy')

MIN_POINTS_FOR_ALIGNMENT = 6

class Scanner:
    @staticmethod
    def ScanImage(gray_img):
        """Searches the image for all Data Matrix, reads and decodes them
        and returns them as a list of DataMatrix objects
        """

        # Determine the plate type from markers in the image
        plate_type = Scanner._determine_plate_type(gray_img)

        # Locate all the barcodes (data matricies) in the image
        finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_img)
        pin_centers = [fp.center for fp in finder_patterns]

        # Align plate (sample holder) model with the image
        geometry = Scanner._get_geometry(gray_img, pin_centers, plate_type)

        # Read all the barcodes (data matricies) in the image
        barcodes = [DataMatrix(fp, gray_img) for fp in finder_patterns]

        return Plate(barcodes, geometry, plate_type)

    @staticmethod
    def _determine_plate_type(image):
        # ToDo: determine from the image
        return "Unipuck"

    @staticmethod
    def _get_geometry(image, pin_centers, plate_type):
        """Align the puck to find the correct slot number for each datamatrix
        """
        if plate_type == "Unipuck":
            geometry = Unipuck(pin_centers)
        elif plate_type == "Square":
            # TODO: implement square sample holders
            geometry = None
        else:
            raise Exception("Unrecognised Sample Plate Type")
        return geometry








