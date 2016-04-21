from __future__ import division

import numpy as np
from pkg_resources import require;

from dls_barcode.datamatrix import DataMatrix, Locator
from dls_barcode.util import Image
from .geometry_unipuck import Unipuck
from .plate import Plate, Slot

require('numpy')


class Scanner:
    @staticmethod
    def ScanSingleImage(gray_img):
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
            plate = Plate(barcodes, geometry, plate_type)
            Scanner._slot_deep_scans(gray_img, plate, finder_patterns)
        else:
            plate = Plate([], geometry, plate_type)

        return plate


    @staticmethod
    def ScanVideoFrame(gray_img, previous_plate):
        # Determine the plate type from markers in the image
        plate_type = Scanner._determine_plate_type(gray_img)

        # Locate all the barcodes (data matricies) in the image
        finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_img)
        pin_centers = [fp.center for fp in finder_patterns]

        # Align plate (sample holder) model with the image
        geometry = Scanner._get_geometry(gray_img, pin_centers, plate_type)

        # If no alignment was possible, just return the previous plate
        if not geometry.is_aligned():
            return previous_plate, False

        # Make a list of the finder patterns with associated slot numbers
        new_finders = [None] * geometry.num_slots
        for fp in finder_patterns:
            slot_num = geometry.containing_slot(fp.center)
            new_finders[slot_num-1] = fp

        # TODO: refactor this function - try to tidy it up a bit, reduce nesting
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
            print("NO COMMON BARCODES") #DEBUG
            remaining_fps = [fp for fp in new_finders if fp is not None]
            barcodes = [DataMatrix(fp, gray_img) for fp in remaining_fps]
            if trial_barcode:
                barcodes.append(trial_barcode)

            any_valid_barcodes = any([dm.is_valid() for dm in barcodes])
            if any_valid_barcodes:
                new_plate = Plate(barcodes, geometry, plate_type)
                Scanner._slot_deep_scans(gray_img, new_plate, finder_patterns)
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
            Scanner._slot_deep_scans(gray_img, plate, finder_patterns)
            return plate, True
    """
    #
    # Working on alternative method where we read a barcode first before performing alignment,
    #   and then using its known location to help with the alignment. Needed because the current
    #   alignment algorithm fails if we cant find any pins in the inner circle on a
    #   particular scan frame.
    #
    @staticmethod
    def ScanVideoFrame(gray_img, previous_plate):
        # Determine the plate type from markers in the image
        plate_type = Scanner._determine_plate_type(gray_img)

        # Locate all the barcodes (data matricies) in the image
        finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_img)
        pin_centers = [fp.center for fp in finder_patterns]

        # Read new barcodes; stop if we find one that matches the previous plate
        has_common_barcode = False
        new_barcodes = []
        for fp in finder_patterns:
            barcode = DataMatrix(fp, gray_img)

            if barcode.is_valid():
                new_barcodes.append(barcode)
                if previous_plate.contains_barcode(barcode.data()):
                    has_common_barcode = True
                    break


        '''
        # Align plate (sample holder) model with the image
        geometry = Scanner._get_geometry(gray_img, pin_centers, plate_type)

        # If no alignment was possible, just return the previous plate
        if not geometry.is_aligned():
            return previous_plate, False

        # Make a list of the finder patterns with associated slot numbers
        new_finders = [None] * geometry.num_slots
        for fp in finder_patterns:
            slot_num = geometry.containing_slot(fp.center)
            new_finders[slot_num-1] = fp
        '''

        # TODO: refactor this function - try to tidy it up a bit, reduce nesting
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
            print("NO COMMON BARCODES") #DEBUG
            remaining_fps = [fp for fp in new_finders if fp is not None]
            barcodes = [DataMatrix(fp, gray_img) for fp in remaining_fps]
            if trial_barcode:
                barcodes.append(trial_barcode)

            any_valid_barcodes = any([dm.is_valid() for dm in barcodes])
            if any_valid_barcodes:
                new_plate = Plate(barcodes, geometry, plate_type)
                Scanner._slot_deep_scans(gray_img, new_plate, finder_patterns)
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
            Scanner._slot_deep_scans(gray_img, plate, finder_patterns)
            return plate, True
    """

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

    @staticmethod
    def _slot_deep_scans(image, plate, finder_patterns, brightness_ratio=5):
        """ Determine if any of the slots in the plate which don't contain barcodes are actually empty
        (i.e. don't contain a pin). If this is the case then mark them as such. If this is not the case
        then it probably means that the slot contains a pin but the locator algorithm was not able to
        locate the finder pattern. If this is the case perform a more detailed search of the area where
        the barcode should be in order to locate it.

        Emoty detection is achieved by examining the average brightness of the slots that we know contain finder
        patterns, and comparing this with the slots that we think are empty. If the slots without an
        identified pin are much less bright than the average then we can infer that they are indeed
        empty (do not contain a pin).
        """
        # Calculate the average brightness of the located barcodes
        pin_brights = []
        for fp in finder_patterns:
            point_in_view = Scanner._image_contains_point(image, fp.center, radius=fp.radius/2)
            if point_in_view:
                brightness = image.calculate_brightness(fp.center, fp.radius / 2)
                pin_brights.append(brightness)

        if any(pin_brights):
            avg_brightness = np.mean(pin_brights)
        else:
            return

        # Calculate average finder pattern radius
        fp_radius = np.mean([fp.radius for fp in finder_patterns])

        # Perform more detailed examination of slots for which we dont have results
        for i, p in enumerate(plate._geometry._template_centers):
            slot = plate.slots[i]

            # If no barcode (and slot is in view), check if slot is empty
            if not slot.contains_barcode():
                point_in_view = Scanner._image_contains_point(image, p, radius=fp_radius/2)
                if point_in_view:
                    brightness = image.calculate_brightness(p, fp_radius / 2)
                    if brightness < avg_brightness / brightness_ratio:
                        slot.empty = True
                    else:
                        slot.empty = False

            # If still no result, do a more careful scan for finder patterns and a more careful read
            if slot.result_not_found() or slot.contains_unreadable_barcode():
                img, _ = image.sub_image(p, fp_radius * 2)

                patterns_deep = list(Locator().locate_datamatrices(img, True, fp_radius))
                patterns = list(Locator().locate_datamatrices(img))

                if len(patterns_deep) > len(patterns):
                    pass#print("deep - " + str(len(patterns_deep)) + " | shallow - " + str(len(patterns)))

                # If we have a valid looking finder pattern from shallow scan, try to use wiggles to read it
                if(len(patterns) > 0):
                    # probably dont need to bother with wiggles in continuous mode but perhaps we can keep a count
                    # of the number of frames so far and then use wiggles if its taking a while.
                    w = 0.25
                    wiggle_offsets = [[0,0], [w, w],[-w,-w],[w,-w],[-w,w]]

                    barcode = DataMatrix(patterns[0], img, offsets=wiggle_offsets)
                    if barcode.is_valid():
                        plate.slots[i] = Slot(i+1, barcode)
                        #print("Good Wiggles - slot " + str(i+1))
                        Scanner.DEBUG_SAVE_IMAGE(img, "shallow_locate_wiggles_read", i)
                    else:
                        Scanner.DEBUG_SAVE_IMAGE(img, "shallow_locate_no_read", i)

                # If we have a valid looking finder pattern from the deep scan, try to read it
                elif len(patterns_deep) > 0:
                    barcode = DataMatrix(patterns_deep[0], img)

                    if barcode.is_valid():
                        plate.slots[i] = Slot(i+1, barcode)
                        #print("Good Deep scan - slot " + str(i+1))
                        Scanner.DEBUG_SAVE_IMAGE(img, "deep_locate_read", i)
                    else:
                        Scanner.DEBUG_SAVE_IMAGE(img, "deep_locate_no_read", i)
                        color = img.to_alpha()
                        for fp in patterns_deep:
                            fp.draw_to_image(color)
                        Scanner.DEBUG_SAVE_IMAGE(color, "deep_locate_no_read_highlight", i)

                # DEBUG - print image of slot if couldn't read anything
                else:
                    Scanner.DEBUG_SAVE_IMAGE(img, "no_locate", i)

    @staticmethod
    def _image_contains_point(image, point, radius=0):
        h, w = image.img.shape
        x, y = point
        return (radius <= x <= w - radius - 1) and (radius <= y <= h - radius - 1)

    @staticmethod
    def DEBUG_SAVE_IMAGE(image, prefix, slotnum):
        import time
        import os
        dir = "../test-output/bad_barcodes/" + prefix + "/"
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = dir + prefix + "_" + str(time.clock()) + "_slot_" + str(slotnum+1) + ".png"
        image.save_as(filename)




