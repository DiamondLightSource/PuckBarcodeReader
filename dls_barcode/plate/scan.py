from __future__ import division

import numpy as np
from pkg_resources import require

from dls_barcode.datamatrix import DataMatrix, Locator
from .geometry_unipuck import Unipuck
from .plate import Plate, Slot

require('numpy')


class AlignmentException(Exception):
    pass


class FrameDiagnostic:
    def __init__(self):
        self.num_finder_patterns = 0
        self.has_barcodes = False
        self.is_aligned = False


class Scanner:
    def __init__(self):
        self.frame_img = None
        self.plate_type = "Unipuck"
        self.num_slots = 16
        self.plate = Plate(self.plate_type, self.num_slots)

    def scan_next_frame(self, frame_img):
        self.frame_img = frame_img

        # Diagnostic object that contains additional info about the scan
        diagnostic = FrameDiagnostic()

        # Locate all the barcodes (data matricies) in the image
        finder_patterns = DataMatrix.LocateAllBarcodesInImage(frame_img)
        diagnostic.num_finder_patterns = len(finder_patterns)

        # Align plate (sample holder) model with the image
        pin_centers = [fp.center for fp in finder_patterns]
        geometry = Unipuck(pin_centers)
        is_aligned = geometry.is_aligned()

        if is_aligned:
            try:
                # Determine if the previous plate scan has any barcodes in common with this one.
                is_same_plate, read_barcodes = self._find_common_barcode(geometry, finder_patterns)
            except AlignmentException:
                # If we have a barcode that matches with the previous frame but that isn't in the same slot, then
                # at least one of the frames wasn't properly aligned.
                is_same_plate = False
                is_aligned = False
                old_num_fps = len(self.plate._geometry._pin_centers)
                new_num_fps = len(finder_patterns)
                print(old_num_fps, new_num_fps)
                # TODO: resolve conflict if alignments don't match - assume one with most points is best

        # If one of the barcodes matches the previous frame and is aligned in the same slot, then we can
        # be fairly sure we are dealing with the same plate. Copy all of the barcodes that we read in the
        # previous late over to their slot in the new plate. Then r toread any that we haven't already read.
        if is_aligned and is_same_plate:
            print("MERGING!!!!!!!!")
            self.plate.merge_fps(geometry, finder_patterns, self.frame_img)
            self._slot_deep_scans(finder_patterns)
            diagnostic.has_barcodes = True

        # If there are no barcodes in common with the previous plate scan, read any that
        # haven't already been read and return a new plate.
        if is_aligned and not is_same_plate:
            print("NEW PLATE")
            used_fps = [barcode._finder_pattern for barcode in read_barcodes]
            remaining_fps = [fp for fp in finder_patterns if fp not in used_fps]
            barcodes = [DataMatrix(fp, frame_img) for fp in remaining_fps]
            barcodes.extend(read_barcodes)

            any_valid_barcodes = any([dm.is_valid() for dm in barcodes])
            diagnostic.has_barcodes = any_valid_barcodes
            if any_valid_barcodes:
                self.plate = Plate(self.plate_type, self.num_slots)
                self.plate.merge_barcodes(geometry, barcodes)
                self._slot_deep_scans(finder_patterns)

        print(self.plate.barcodes())

        diagnostic.is_aligned = is_aligned
        return self.plate, diagnostic

    def _find_common_barcode(self, geometry, finder_patterns):
        """ Determine if the set of finder patterns has any barcodes in common with the existing plate.
        Return a boolean and a list of the barcodes that have been read. """
        read_barcodes = []
        has_common_barcodes = False

        if self.plate is None:
            return has_common_barcodes, read_barcodes

        # Make a list of the finder patterns with associated slot numbers
        slotted_fps = [None] * geometry.num_slots
        for fp in finder_patterns:
            slot_num = geometry.containing_slot(fp.center)
            slotted_fps[slot_num-1] = fp

        # Determine if the previous plate scan has any barcodes in common with this one.
        for i in range(self.plate.num_slots):
            old_slot = self.plate.slot(i)
            new_fp = slotted_fps[i-1]
            # Search through valid barcodes until we find a match
            if (old_slot.state() == Slot.VALID) and (new_fp is not None):
                # If we have a finder pattern in the same slot, try to read it. If it matches the previous barcode,
                # then we have one in common, if it doesn't then we have a completely new plate. If we cant read
                # the barcode, carry on looking for a match
                barcode = DataMatrix(new_fp, self.frame_img)
                read_barcodes.append(barcode)

                if barcode.is_valid():
                    # If it matches we have a common barcode, if not we have a clash; break either way
                    if barcode.data() == old_slot.get_barcode():
                        has_common_barcodes = True
                    elif self.plate.contains_barcode(barcode.data()):
                        print("ALIGNMENT ERROR - ", barcode.data(), old_slot.get_barcode(), i)
                        raise AlignmentException("Alignment Error")

        return has_common_barcodes, read_barcodes

    def _slot_deep_scans(self, finder_patterns, brightness_ratio=5):
        """ Determine if any of the slots in the plate which don't contain barcodes are actually empty
        (i.e. don't contain a pin). If this is the case then mark them as such. If this is not the case
        then it probably means that the slot contains a pin but the locator algorithm was not able to
        locate the finder pattern. If this is the case perform a more detailed search of the area where
        the barcode should be in order to locate it.

        Empty detection is achieved by examining the average brightness of the slots that we know contain finder
        patterns, and comparing this with the slots that we think are empty. If the slots without an
        identified pin are much less bright than the average then we can infer that they are indeed
        empty (do not contain a pin).
        """
        # Calculate the average brightness of the located barcodes
        avg_brightness = self._calculate_average_pin_brightness(finder_patterns)
        brightness_threshold = avg_brightness / brightness_ratio

        # Calculate average finder pattern radius
        fp_radius = np.mean([fp.radius for fp in finder_patterns])

        # Perform more detailed examination of slots for which we don't have results
        slot_centers = self.plate._geometry._template_centers
        for i, p in enumerate(slot_centers):
            slot = self.plate.slot(i+1)

            # If we cant see the slot in the current frame, continue to next slot
            slot_in_frame = Scanner._image_contains_point(self.frame_img, p, radius=fp_radius/2)
            if not slot_in_frame:
                continue

            # If no valid barcode, check if slot is empty
            state = slot.state()
            if state != Slot.VALID:
                brightness = self.frame_img.calculate_brightness(p, fp_radius / 2)
                if brightness < brightness_threshold:
                    slot.set_empty()
                elif state == Slot.EMPTY:
                    slot.set_no_result()

            # If still no result, do a more careful scan for finder patterns and a more careful read
            state = slot.state()
            if state == Slot.NO_RESULT or state == Slot.UNREADABLE:
                slot_img, _ = self.frame_img.sub_image(p, fp_radius * 2)

                patterns_deep = list(Locator().locate_datamatrices(slot_img, True, fp_radius))
                patterns = list(Locator().locate_datamatrices(slot_img))

                if len(patterns_deep) > len(patterns):
                    pass#print("deep - " + str(len(patterns_deep)) + " | shallow - " + str(len(patterns)))

                # If we have a valid looking finder pattern from shallow scan, try to use wiggles to read it
                if(len(patterns) > 0):
                    # probably don't need to bother with wiggles in continuous mode but perhaps we can keep a count
                    # of the number of frames so far and then use wiggles if its taking a while.
                    w = 0.25
                    wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]

                    barcode = DataMatrix(patterns[0], slot_img, offsets=wiggle_offsets)
                    if barcode.is_valid():
                        slot.set_barcode(barcode)
                        print("Good Wiggles - slot " + str(i+1))
                        Scanner.DEBUG_SAVE_IMAGE(slot_img, "shallow_locate_wiggles_read", i)
                    else:
                        Scanner.DEBUG_SAVE_IMAGE(slot_img, "shallow_locate_no_read", i)

                # If we have a valid looking finder pattern from the deep scan, try to read it
                elif len(patterns_deep) > 0:
                    w = 0.25
                    wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]

                    barcode = DataMatrix(patterns_deep[0], slot_img, wiggle_offsets)

                    if barcode.is_valid():
                        slot.set_barcode(barcode)
                        print("Good Deep scan - slot " + str(i+1))
                        Scanner.DEBUG_SAVE_IMAGE(slot_img, "deep_locate_read", i)
                    else:
                        Scanner.DEBUG_SAVE_IMAGE(slot_img, "deep_locate_no_read", i)
                        color = slot_img.to_alpha()
                        for fp in patterns_deep:
                            fp.draw_to_image(color)
                        Scanner.DEBUG_SAVE_IMAGE(color, "deep_locate_no_read_highlight", i)

                # DEBUG - print image of slot if couldn't read anything
                else:
                    Scanner.DEBUG_SAVE_IMAGE(slot_img, "no_locate", i)

    def _calculate_average_pin_brightness(self, finder_patterns):
        # Calculate the average brightness of the located barcodes
        pin_brights = []
        for fp in finder_patterns:
            center_in_frame = Scanner._image_contains_point(self.frame_img, fp.center, radius=fp.radius/2)
            if center_in_frame:
                brightness = self.frame_img.calculate_brightness(fp.center, fp.radius / 2)
                pin_brights.append(brightness)

        if any(pin_brights):
            avg_brightness = np.mean(pin_brights)
        else:
            avg_brightness = 0

        return avg_brightness

    @staticmethod
    def _image_contains_point(image, point, radius=0):
        h, w = image.img.shape
        x, y = point
        return (radius <= x <= w - radius - 1) and (radius <= y <= h - radius - 1)

    @staticmethod
    def DEBUG_SAVE_IMAGE(image, prefix, slotnum):
        return

        import time
        import os
        dir = "../test-output/bad_barcodes/" + prefix + "/"
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = dir + prefix + "_" + str(time.clock()) + "_slot_" + str(slotnum+1) + ".png"
        image.save_as(filename)




