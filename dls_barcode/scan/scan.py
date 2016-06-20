from __future__ import division

from pkg_resources import require

from dls_barcode.datamatrix import DataMatrix
from dls_barcode.scan.slot_scan import SlotScanner
from dls_barcode.plate.geometry_unipuck import Unipuck
from dls_barcode.plate.plate import Plate, Slot
from .geometry_adjuster import GeometryAdjuster


require('numpy')


class AlignmentException(Exception):
    pass


class FrameDiagnostic:
    def __init__(self):
        self.num_finder_patterns = 0
        self.has_barcodes = False
        self.is_aligned = False


class Scanner:
    def __init__(self, options):
        self.frame_img = None
        self.plate_type = "Unipuck"
        self.num_slots = 16
        self.plate = Plate(self.plate_type, self.num_slots)

        self._options = options

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
        slot_scanner = SlotScanner(frame_img, barcodes, self._options)

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
            geometry = self._adjust_geometry(barcodes)
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

    def _adjust_geometry(self, barcodes):
        adjuster = GeometryAdjuster()
        geometry = adjuster.adjust(self.plate, barcodes)
        return geometry
