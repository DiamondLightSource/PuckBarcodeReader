import random

from plate.slot import Slot


class BadGeometryException(Exception):
    pass


class PlateScanner:
    FRAMES_BEFORE_DEEP = 3

    def __init__(self, plate, single_frame=False):
        self._plate = plate

        self._frame_num = -1
        self._force_deep_scan = single_frame

    def new_frame(self, geometry, barcodes, slot_scanner):
        """ Merge the set of barcodes from a new scan into the plate. The new set comes from a new image
        of the same plate, so will almost certainly contain many of the same barcodes. Actually reading a
        barcode is relatively expensive; we iterate through each slot in the plate and only attempt to
        perform a read if we don't already have valid barcode data for the slot.

        For each new frame we update the slot bounds (center, radius) with that calculated by the geometry
        object and update the slot position with the actual position of the center of the barcode. The
        position is likely to be similar to, but not exactly the same as, the bound's center. This info
        is retained as it allows us to properly calculate the geometry for future frames.
        """
        self._frame_num += 1
        self._plate.set_geometry(geometry)

        # Fill each slot with the correct barcodes
        for slot in self._plate.slots():
            self._new_slot_frame(barcodes, slot, slot_scanner)

    def _new_slot_frame(self, barcodes, slot, slot_scanner):
        slot.new_frame()

        # Find the barcode from the new set that is in the slot position
        bounds = slot.bounds()
        barcode = self._find_matching_barcode(bounds, barcodes)

        # Update the barcode position - use the actual position of the barcode if available,
        # otherwise use the slot center position (from geometry) as an approximation
        position = barcode.center() if barcode else bounds.center()
        slot.set_barcode_position(position)

        # If we haven't already found this barcode data, try to read it from the new barcode
        if slot.state() != Slot.VALID and barcode:
            barcode.perform_read()
            slot.set_barcode(barcode)

        # If the barcode still hasn't been read, try a deeper slot scan
        self._slot_scan(slot, slot_scanner)

    @staticmethod
    def _find_matching_barcode(slot_bounds, barcodes):
        for bc in barcodes:
            if slot_bounds.contains_point(bc.center()):
                return bc
        return None

    def _slot_scan(self, slot, slot_scanner):
        # If the slot barcode has already been read correctly, skip it
        if slot.state() == Slot.VALID:
            return

        # Check for empty slot
        if slot_scanner.is_slot_empty(slot):
            slot.set_empty()
            return

        # Clear any previous (empty/unread) result
        slot.set_no_result()

        if self._should_do_deep_scan():
            self._perform_deep_contour_slot_scan(slot, slot_scanner, self._force_deep_scan)
            self._perform_square_slot_scan(slot, slot_scanner)

    def _should_do_deep_scan(self):
        return self._force_deep_scan or self._frame_num > self.FRAMES_BEFORE_DEEP

    @staticmethod
    def _perform_deep_contour_slot_scan(slot, slot_scanner, force_all):
        if slot.state() != Slot.VALID:
            barcodes = slot_scanner.deep_scan(slot)

            # Pick a random finder pattern from those returned
            if not force_all and barcodes:
                barcodes = [random.choice(barcodes)]

            for barcode in barcodes:
                slot_scanner.wiggles_read(barcode, "DEEP CONTOUR")
                slot.set_barcode(barcode)
                if barcode.is_valid():
                    break

    @staticmethod
    def _perform_square_slot_scan(slot, slot_scanner):
        if slot.state() != Slot.VALID:
            barcode = slot_scanner.square_scan(slot)
            if barcode is not None:
                slot_scanner.wiggles_read(barcode, "SQUARE")
                slot.set_barcode(barcode)
