from __future__ import division
from dls_barcode.datamatrix import DataMatrix
from unipuck import Unipuck
from plate import Plate

from pkg_resources import require;  require('numpy')


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
        if geometry.is_aligned():
            barcodes = [DataMatrix(fp, gray_img) for fp in finder_patterns]
        else:
            barcodes = []

        return Plate(barcodes, geometry, plate_type)

    @staticmethod
    def ScanImageContinuous(gray_img, previous_plate):
        # Determine the plate type from markers in the image
        plate_type = Scanner._determine_plate_type(gray_img)

        # Locate all the barcodes (data matricies) in the image
        finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_img)
        pin_centers = [fp.center for fp in finder_patterns]

        # Align plate (sample holder) model with the image
        geometry = Scanner._get_geometry(gray_img, pin_centers, plate_type)

        # If no alignment was possible, just return the previous plate
        if not geometry.aligned:
            return previous_plate

        # Make a list of the finder patterns with associated slot numbers
        new_slots = [None] * geometry.num_slots
        for fp in finder_patterns:
            slot_num = geometry.closest_slot(fp.center)
            new_slots[slot_num] = fp

        # Create list to store new barcodes
        new_barcodes = []

        # Determine if the previous plate scan has any barcodes in common with this one.
        has_common_barcode = False
        for old_slot in previous_plate.slots:
            # Search through valid barcodes until we find a match
            if old_slot.contains_valid_barcode():
                num = old_slot.number

                # If we have a finder pattern in the same slot, try to read it. If it matches the previous barcode,
                # then we have one in common, if it doesn't then we have a completely new plate. If we cant read
                # the barcode, carry on looking for a match
                if new_slots[num] is not None:
                    dm = DataMatrix(new_slots[num], gray_img)
                    # Record the barcode and remove the used finder pattern so we don't read it again
                    new_barcodes.append(dm)
                    new_slots[num] = None
                    if dm.is_valid():
                        # If it matches we have a common barcode, if not we have a clash; break either way
                        if dm.data() == old_slot.get_barcode():
                            has_common_barcode = True
                        break

        # If there are no barcodes in common with the previous plate scan, read any that
        # haven't already been read and return a new plate
        if not has_common_barcode:
            remaining_fps = [s for s in new_slots if s is not None]
            barcodes = [DataMatrix(fp, gray_img) for fp in remaining_fps]
            barcodes.extend(new_barcodes)

        else:
            # TODO: case where they have barcodes in common - could do this in the earlier for loop
            # Combine old barcodes with new and create a new plate
            for old_slot in previous_plate.slots:
                pass



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
            raise Exception("Geometry not yet implemented")
        else:
            raise Exception("Unrecognised Sample Plate Type")

        return geometry








