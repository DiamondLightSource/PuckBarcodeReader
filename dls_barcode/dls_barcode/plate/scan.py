from __future__ import division
from dls_barcode.datamatrix import DataMatrix
from unipuck import Unipuck
from plate import Plate, Slot

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
            return previous_plate, False

        # Make a list of the finder patterns with associated slot numbers
        new_finders = [None] * geometry.num_slots
        for fp in finder_patterns:
            slot_num = geometry.closest_slot(fp.center)
            new_finders[slot_num-1] = fp

        # Determine if the previous plate scan has any barcodes in common with this one.
        has_common_barcode = False
        trial_barcode = None
        for i, old_slot in enumerate(previous_plate.slots):
            # Search through valid barcodes until we find a match
            if (old_slot.contains_valid_barcode()) and (new_finders[i] is not None):
                # If we have a finder pattern in the same slot, try to read it. If it matches the previous barcode,
                # then we have one in common, if it doesn't then we have a completely new plate. If we cant read
                # the barcode, carry on looking for a match
                trial_barcode = DataMatrix(new_finders[i], gray_img)
                # Remove the used finder pattern so we don't read it again
                new_finders[i] = None
                if trial_barcode.is_valid():
                    # If it matches we have a common barcode, if not we have a clash; break either way
                    if trial_barcode.data() == old_slot.get_barcode():
                        has_common_barcode = True
                    break

        # If there are no barcodes in common with the previous plate scan, read any that
        # haven't already been read and return a new plate
        if not has_common_barcode:
            remaining_fps = [fp for fp in new_finders if fp is not None]
            barcodes = [DataMatrix(fp, gray_img) for fp in remaining_fps]
            if trial_barcode:
                barcodes.append(trial_barcode)

            any_valid_barcodes = any([dm.is_valid() for dm in barcodes])
            if any_valid_barcodes:
                new_plate = Plate(barcodes, geometry, plate_type)
                return new_plate, any_valid_barcodes
            else:
                return previous_plate, any_valid_barcodes

        else:
            plate = Plate(barcodes=[], geometry=geometry, type=plate_type)
            # Combine old barcodes with new and create a new plate
            for i, old_slot in enumerate(previous_plate.slots):
                if (old_slot.contains_valid_barcode()) or (new_finders[i] is None):
                    plate.slots[i] = old_slot
                else:
                    dm = DataMatrix(new_finders[i], gray_img)
                    plate.slots[i] = Slot(i+1, dm)
            plate._sort_slots()
            return plate, True


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








