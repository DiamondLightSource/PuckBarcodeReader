from __future__ import division

import numpy as np
from pkg_resources import require

from dls_barcode.datamatrix import DataMatrix
from dls_barcode.util import Transform
from .geometry_unipuck import Unipuck
from .plate import Plate, Slot
from .slot_scan import SlotScanner


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

    def scan_next_frame(self, frame_img, single_image=False):
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

        # Create slot scanner
        slot_scanner = SlotScanner(frame_img, barcodes)

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
                self.plate.initialize_from_barcodes(geometry, barcodes, slot_scanner, single_image)

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
            self.plate.merge_new_frame(geometry, barcodes, slot_scanner)
            diagnostic.has_barcodes = True

        print(self.plate.total_frames, self.plate.barcodes())  # DEBUG

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

        return has_common_barcodes, has_common_geometry

    def _adjust_alignment(self, barcodes):
        # TODO: document this method

        # If we don't have 2 common barcodes, we can't realign, so return a blank geometry (which
        # will cause this frame to be skipped).
        valid_barcodes = [bc for bc in barcodes if bc.is_read() and bc.is_valid()]
        if len(valid_barcodes) < 2:
            print("ALIGNMENT ADJUSTMENT FAIL")  # DEBUG
            return Unipuck([])

        print("ALIGNMENT ADJUSTMENT")  # DEBUG

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





