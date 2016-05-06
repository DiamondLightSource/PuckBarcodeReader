from __future__ import division

import numpy as np
from pkg_resources import require

from dls_barcode.datamatrix import DataMatrix
from dls_barcode.util import Transform
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
        barcodes = DataMatrix.LocateAllBarcodesInImage(frame_img)
        diagnostic.num_finder_patterns = len(barcodes)

        # Align plate (sample holder) model with the image
        bc_centers = [bc.center() for bc in barcodes]
        geometry = Unipuck(bc_centers)
        is_aligned = geometry.is_aligned()

        # ---------- READ SOME BARCODES ----------------------
        if is_aligned:
            # Determine if the previous plate scan has any barcodes in common with this one.
            is_same_plate, is_same_align = self._find_common_barcode(geometry, barcodes)

        # ------------- NEW PLATE? ----------------------------
        # If there are no barcodes in common with the previous plate scan, read any that
        # haven't already been read and return a new plate.
        if is_aligned and not is_same_plate:
            for bc in barcodes:
                bc.perform_read()

            any_valid_barcodes = any([bc.is_valid() for bc in barcodes])
            diagnostic.has_barcodes = any_valid_barcodes
            if any_valid_barcodes:
                self.plate = Plate(self.plate_type, self.num_slots)
                self.plate.initialize_from_barcodes(geometry, barcodes)
                self._slot_deep_scans(barcodes)

        # ------------- ADJUST ALIGNMENT -------------------
        if is_aligned and is_same_plate and not is_same_align:
            # If we have a barcode that matches with the previous frame but that isn't in the same slot, then
            # at least one of the frames wasn't properly aligned.
            geometry = self._adjust_alignment(barcodes)
            is_aligned = geometry.is_aligned()

        # ------------- SAME PLATE? --------------------------
        # If one of the barcodes matches the previous frame and is aligned in the same slot, then we can
        # be fairly sure we are dealing with the same plate. Copy all of the barcodes that we read in the
        # previous plate over to their slot in the new plate. Then read any that we haven't already read.
        if is_aligned and is_same_plate:
            self.plate.merge_new_frame(geometry, barcodes)
            self._slot_deep_scans(barcodes)
            diagnostic.has_barcodes = True

        print(self.plate.barcodes())  # DEBUG

        diagnostic.is_aligned = is_aligned
        return self.plate, diagnostic

    def _find_common_barcode(self, geometry, unread_barcodes):
        """ Determine if the set of finder patterns has any barcodes in common with the existing plate.
        Return a boolean and a list of the barcodes that have been read. """
        has_common_barcodes = False
        has_common_geometry = False
        num_common_barcodes = 0

        # If no plate, don't bother to look for common barcodes
        if self.plate is None:
            return has_common_barcodes, has_common_geometry

        # Make a list of the unread barcodes with associated slot numbers - from this frame's geometry
        slotted_bcs = [None] * geometry.num_slots
        for bc in unread_barcodes:
            slot_num = geometry.containing_slot(bc.center())
            slotted_bcs[slot_num-1] = bc

        # Determine if the previous plate scan has any barcodes in common with this one.
        for i in range(self.plate.num_slots):
            old_slot = self.plate.slot(i)
            new_bc = slotted_bcs[i-1]

            # Only interested in finding barcodes that match existing ones
            if new_bc is None or old_slot.state() != Slot.VALID:
                continue

            # Read the barcode
            new_bc.perform_read()

            if not new_bc.is_valid():
                continue

            num_common_barcodes += 1
            has_common_geometry = new_bc.data() == old_slot.barcode_data()
            has_common_barcodes = has_common_geometry or self.plate.contains_barcode(new_bc.data())

            # If the geometry of this and the previous frame line up, then we are done. Otherwise we
            # need to read at least 2 barcodes so we can perform a realignment.
            if has_common_geometry or num_common_barcodes >= 2:
                break

        # todo: case where we have common barcodes but not common geometry and only 1 common barcode
        return has_common_barcodes, has_common_geometry

    def _adjust_alignment(self, barcodes):
        # TODO: document this method
        # Get the two common barcodes
        valid_barcodes = [bc for bc in barcodes if bc.is_read() and bc.is_valid()]
        if len(valid_barcodes) != 2:  # DEBUG
            raise Exception("Not enough barcodes to perform realignment")

        print("ALIGNMENT ADJUSTMENT")

        # Get the positions of the two common barcodes in the current frame and the previous one
        barcode_a = valid_barcodes[0]
        barcode_b = valid_barcodes[1]
        pos_a_new = barcode_a.center()
        pos_b_new = barcode_b.center()
        pos_a_old = None
        pos_b_old = None

        for slot in self.plate._slots:
            if slot.barcode_data() == barcode_a.data():
                pos_a_old = slot.barcode_position()
            elif slot.barcode_data() == barcode_b.data():
                pos_b_old = slot.barcode_position()

        # Determine the transformation that maps the old points to the new
        line_transform = Transform.line_mapping(pos_a_old, pos_b_old, pos_a_new, pos_b_new)

        # Transform all old space bc centers to new space
        transformed_bc_centers = []
        for slot in self.plate._slots:
            center = slot.barcode_position()
            if center:
                transformed_center = line_transform.transform(center)
                transformed_bc_centers.append(transformed_center)

        # Replace any transformed points which overlap new fp centers
        new_centers = [bc.center() for bc in barcodes]
        radius_sq = np.mean([bc.radius() for bc in barcodes]) ** 2
        for old_center in transformed_bc_centers:
            overlap = False
            for bc in barcodes:
                new_center = bc.center()
                distance = (new_center[0] - old_center[0])**2 + (new_center[1] - old_center[1])**2
                if distance < radius_sq:
                    overlap = True

            if not overlap:
                new_centers.append(old_center)

        # Create a new geometry from the new set of fp centers
        geometry = Unipuck(new_centers)

        return geometry

    def _slot_deep_scans(self, barcodes, brightness_ratio=5):
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
        avg_brightness = self._calculate_average_pin_brightness(barcodes)
        brightness_threshold = avg_brightness / brightness_ratio

        # Calculate average barcode radius
        bc_radius = np.mean([bc.radius() for bc in barcodes])

        # Perform more detailed examination of slots for which we don't have results
        for slot in self.plate._slots:
            center = slot.barcode_position()
            state = slot.state()

            # If the slot barcode has already been read correctly, skip it
            if state == Slot.VALID:
                continue

            # If we cant see the slot in the current frame, skip it
            slot_in_frame = Scanner._image_contains_point(self.frame_img, center, radius=bc_radius/2)
            if not slot_in_frame:
                continue

            # Check if slot is empty
            brightness = self.frame_img.calculate_brightness(center, bc_radius / 2)
            if brightness < brightness_threshold:
                slot.set_empty()
            elif state == Slot.EMPTY:
                slot.set_no_result()

            '''
            # If still no result, do a more careful scan for finder patterns and a more careful read
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

            '''

    def _calculate_average_pin_brightness(self, barcodes):
        """ Calculate the brightness of a small area at each barcode and return the average value.
        A barcode will be much brighter than an empty slot as it usually contains plenty of white
        pixels. This allows us to distinguish between an empty slot with no pin, and a slot with a pin
        where we just haven't been able to locate the barcode.
        """
        pin_brights = []
        for bc in barcodes:
            center_in_frame = Scanner._image_contains_point(self.frame_img, bc.center(), radius=bc.radius()/2)
            if center_in_frame:
                brightness = self.frame_img.calculate_brightness(bc.center(), bc.radius() / 2)
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




