from __future__ import division

from dls_barcode.datamatrix import DataMatrix
from dls_barcode.plate.geometry_unipuck import Unipuck
from dls_barcode.plate.plate import Plate, Slot
from .geometry_adjuster import GeometryAdjuster
from .slot_scan import SlotScanner


class AlignmentException(Exception):
    pass


class FrameDiagnostic:
    def __init__(self):
        self.num_finder_patterns = 0
        self.has_barcodes = False
        self.is_aligned = False


class Scanner:
    def __init__(self, options):
        self.plate_type = "Unipuck"
        self.num_slots = 16
        self.plate = Plate(self.plate_type, self.num_slots)

        self._options = options

        self._frame_img = None
        self._geometry = None
        self._barcodes = None
        self._is_single_image = False

    def get_frame_diagnostic(self):
        diagnostic = FrameDiagnostic()
        diagnostic.num_finder_patterns = len(self._barcodes)
        diagnostic.is_aligned = self._is_geometry_aligned()
        diagnostic.has_barcodes = self._any_valid_barcodes()
        return diagnostic

    def scan_next_frame(self, frame_img, is_single_image=False):
        self._reset_for_new_frame()

        self._frame_img = frame_img
        self._is_single_image = is_single_image

        self._barcodes = self._locate_all_barcodes_in_image(frame_img)
        self._geometry = self._create_geometry_from_barcodes()

        if self._is_geometry_aligned():
            # Determine if the previous plate scan has any barcodes in common with this one.
            has_common_barcodes, is_same_align = self._find_common_barcode(self._geometry, self._barcodes)

            if has_common_barcodes and not is_same_align:
                self._geometry = self._adjust_geometry(self._barcodes)
            elif not has_common_barcodes:
                self._initialize_plate_from_barcodes()

        # ------------- SAME PLATE? --------------------------
        if self._is_geometry_aligned() and has_common_barcodes:
            self._merge_frame_into_plate()

        if self._options.console_barcodes.value():
            print(self.plate.barcodes())

        return self.plate

    def _reset_for_new_frame(self):
        self._frame_img = None
        self._geometry = None
        self._barcodes = None
        self._is_single_image = False

    def _locate_all_barcodes_in_image(self, frame_img):
        return DataMatrix.LocateAllBarcodesInImage(frame_img)

    def _create_geometry_from_barcodes(self):
        bc_centers = [bc.center() for bc in self._barcodes]
        return Unipuck.from_pin_centers(bc_centers)

    def _initialize_plate_from_barcodes(self):
        for bc in self._barcodes:
            bc.perform_read()

        if self._any_valid_barcodes():
            slot_scanner = self._create_slot_scanner()
            self.plate = Plate(self.plate_type, self.num_slots)
            self.plate.initialize_from_barcodes(self._geometry, self._barcodes,
                                                slot_scanner, self._is_single_image)

    def _merge_frame_into_plate(self):
        # If one of the barcodes matches the previous frame and is aligned in the same slot, then we can
        # be fairly sure we are dealing with the same plate. Copy all of the barcodes that we read in the
        # previous plate over to their slot in the new plate. Then read any that we haven't already read.
        slot_scanner = self._create_slot_scanner()
        self.plate.merge_new_frame(self._geometry, self._barcodes, slot_scanner)

    def _is_geometry_aligned(self):
        return self._geometry.is_aligned()

    def _any_valid_barcodes(self):
        return any([bc.is_read() and bc.is_valid() for bc in self._barcodes])

    def _create_slot_scanner(self):
        slot_scanner = SlotScanner(self._frame_img, self._barcodes, self._options)
        return slot_scanner

    def _find_common_barcode(self, geometry, barcodes):
        """ Determine if the set of finder patterns has any barcodes in common with the existing plate.
        Return a boolean and a list of the barcodes that have been read. """
        has_common_barcodes = False
        has_common_geometry = False
        num_common_barcodes = 0

        # If no plate, don't bother to look for common barcodes
        if self.plate is None:
            return has_common_barcodes, has_common_geometry

        slotted_barcodes = self._make_slotted_barcodes_list(barcodes, geometry)

        # Determine if the previous plate scan has any barcodes in common with this one.
        for i in range(self.plate.num_slots):
            old_slot = self.plate.slot(i)
            new_bc = slotted_barcodes[i-1]

            # Only interested in reading barcodes that might match existing ones
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

    def _make_slotted_barcodes_list(self, barcodes, geometry):
        # Make a list of the unread barcodes with associated slot numbers - from this frame's geometry
        slotted_bcs = [None] * geometry.num_slots
        for bc in barcodes:
            slot_num = geometry.containing_slot(bc.center())
            slotted_bcs[slot_num - 1] = bc

        return slotted_bcs

    def _adjust_geometry(self, barcodes):
        # If we have a barcode that matches with the previous frame but that isn't in the same slot, then
        # at least one of the frames wasn't properly aligned - so we adjust the geometry to match the
        # frames together
        adjuster = GeometryAdjuster()
        geometry = adjuster.adjust(self.plate, barcodes)
        return geometry
