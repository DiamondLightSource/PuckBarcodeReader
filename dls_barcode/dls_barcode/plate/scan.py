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
        symbol_locations = [fp.bounds() for fp in finder_patterns]

        # Align plate (sample holder) model with the image
        aligner = Aligner()
        geometry = aligner.get_geometry(gray_img, symbol_locations, plate_type)

        # Read all the barcodes (data matricies) in the image
        barcodes = DataMatrix.ReadAllBarcodesInImage(gray_img, finder_patterns)

        return Plate(barcodes, geometry, plate_type)

    @staticmethod
    def _determine_plate_type(image):
        # ToDo: determine from the image
        return "Unipuck"


class Aligner:
    def get_geometry(self, image, symbol_locations, plate_type):
        """Align the puck to find the correct slot number for each datamatrix
        """
        if plate_type == "Unipuck":
            geometry = self._get_unipuck_geometry(image, symbol_locations)
        elif plate_type == "Square":
            geometry = self._get_square_geometry(image, symbol_locations)
        else:
            raise Exception("Unrecognised Sample Plate Type")
        return geometry

    def _get_unipuck_geometry(self, image, symbol_locations):
        # Find the average radius of the barcode symbols
        radii = [r for (c, r) in symbol_locations]
        avg_radius = sum(radii) / len(radii)

        uncircled_pins = []
        pin_circles = []
        pin_rois = [];
        for (center, radius) in symbol_locations:
            # Get region of image that fully contains the pin
            r = 2.5 * radius
            sub_img, roi = CvImage.sub_image(image, center, r)
            pin_rois.append(roi)

            # Find circle in the sub image
            circle = CvImage.find_circle(sub_img, avg_radius, 2*avg_radius)
            if circle:
                circle[0][0] += roi[0]
                circle[0][1] += roi[1]
                pin_circles.append(circle)
            else:
                uncircled_pins.append(center)

        if not pin_circles:
            raise Exception("No puck slots detected")
        elif len(pin_circles) < MIN_POINTS_FOR_ALIGNMENT:
            raise Exception("Not enough barcodes for alignment")

        # Create representation of the puck geometry based on positions of the pins
        geometry = Unipuck(pin_circles, pin_rois, uncircled_pins)
        return geometry

    def _get_square_geometry(self, image, barcodes):
        # ToDo: implement square sample holders
        return None







