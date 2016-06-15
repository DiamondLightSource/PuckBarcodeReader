import uuid
import random

from dls_barcode.util import Color
from .slot import Slot, EMPTY_SLOT_SYMBOL, NOT_FOUND_SLOT_SYMBOL


class BadGeometryException(Exception):
    pass


class Plate:
    """ Represents a sample holder plate.
    """
    def __init__(self, plate_type="Unipuck", num_slots=16):
        self.total_frames = 0
        self.id = str(uuid.uuid1())

        self.num_slots = num_slots
        self.type = plate_type
        self.error = None
        self._geometry = None

        # Initialize slots
        self._slots = [Slot(i) for i in range(1, self.num_slots+1)]

    def initialize_from_barcodes(self, geometry, barcodes, slot_scanner, single_frame=False):
        """ Initialize the plate with the set of barcodes from the scan of a new frame. The position
        of each slot (in the image) has already been calculated in the Geometry object. We store this
        calculated position as well as the actual center position of the barcode itself in the slot
        object. This allows us to properly determine which barcode goes in which slot in subsequent
        image frames, even if the sample holder has been moved around.
        """
        if not geometry.is_aligned:
            raise BadGeometryException("Could not assign barcodes to slots as geometry not aligned.")

        # Fill each slot with the correct barcodes
        for slot in self._slots:
            slot.new_frame()

            slot_num = slot.number()
            bounds = geometry.slot_bounds(slot_num)
            barcode = _find_matching_barcode(bounds, barcodes)
            position = barcode.center() if barcode else bounds[0]

            slot.set_bounds(bounds)
            slot.set_barcode(barcode)
            slot.set_barcode_position(position)

            self._slot_scan(slot, slot_scanner, force=single_frame)

        self._geometry = geometry
        self.error = geometry.error
        self.total_frames += 1

    def merge_new_frame(self, geometry, new_barcodes, slot_scanner):
        """ Merge the set of barcodes from a new scan into this plate. The new set comes from a new image
        of the same plate, so will almost certainly contain many of the same barcodes. Actually reading a
        barcode is relatively expensive; we iterate through each slot in the plate and only attempt to
        perform a read if we don't already have valid barcode data for the slot.

        For each new frame we update the slot bounds (center, radius) with that calculated by the geometry
        object and update the slot position with the actual position of the center of the barcode. The
        position is likely to be similar to, but not exactly the same as, the bound's center. This info
        is retained as it allows us to properly calculate the geometry for future frames.
        """
        # Set the frame count
        self.total_frames += 1

        if not geometry.is_aligned:
            raise BadGeometryException("Could not assign barcodes to slots as geometry not aligned.")

        for slot in self._slots:
            slot.new_frame()

            slot_num = slot.number()
            state = slot.state()

            # Set slot bounds - as determined by the geometry
            bounds = geometry.slot_bounds(slot_num)
            slot.set_bounds(bounds)

            # Find the barcode from the new set that is in the slot position
            barcode = _find_matching_barcode(bounds, new_barcodes)

            # Update the barcode position - use the actual position of the new barcode if available,
            # otherwise use the slot center position (from geometry) as an approximation
            if barcode:
                slot.set_barcode_position(barcode.center())
            else:
                slot.set_barcode_position(bounds[0])

            # If we haven't already found this barcode data, try to read it from the new barcode
            if state != Slot.VALID and barcode:
                barcode.perform_read()
                slot.set_barcode(barcode)
            elif state == Slot.UNREADABLE:
                slot.set_barcode(None)

            self._slot_scan(slot, slot_scanner)

        self._geometry = geometry
        self.error = geometry.error

    def _slot_scan(self, slot, slot_scanner, force=False):

        # If the slot barcode has already been read correctly, skip it
        if slot.state() == Slot.VALID:
            return

        do_empty_check = True
        do_deep = force or self.total_frames > 3
        do_square = force or self.total_frames > 3

        # Check for empty slot
        if do_empty_check:
            if slot_scanner.is_slot_empty(slot):
                slot.set_empty()
                return

        if do_deep:
            # Careful look for finder patterns
            if slot.state() != Slot.VALID:
                barcodes = slot_scanner.deep_scan(slot)

                # Pick a random finder pattern from those returned
                if not force and barcodes:
                    barcodes = [random.choice(barcodes)]

                for barcode in barcodes:
                    slot_scanner.wiggles_read(barcode, "DEEP CONTOUR")
                    slot.set_barcode(barcode)
                    if barcode.is_valid():
                        break

        if do_square:
            if slot.state() != Slot.VALID:
                barcode = slot_scanner.square_scan(slot)
                if barcode is not None:
                    slot_scanner.wiggles_read(barcode, "SQUARE")
                    slot.set_barcode(barcode)

    #########################
    # ACCESSOR FUNCTIONS
    #########################
    def slot(self, i):
        """ Get the numbered slot on this sample plate."""
        return self._slots[i - 1]

    def barcodes(self):
        """ Returns a list of barcode strings. Empty slots are represented by the empty string.
        """
        return [slot.barcode_data() for slot in self._slots]

    #########################
    # STATUS FUNCTIONS
    #########################
    def num_empty_slots(self):
        return len([slot for slot in self._slots if slot.state() == Slot.EMPTY])

    def num_valid_barcodes(self):
        return len([slot for slot in self._slots if slot.state() == Slot.VALID])

    def num_unread_barcodes(self):
        return self.num_slots - self.num_valid_barcodes() - self.num_empty_slots()

    def is_full_valid(self):
        return (self.num_valid_barcodes() + self.num_empty_slots()) == self.num_slots

    def contains_barcode(self, barcode):
        """ Returns true if the plate contains a slot with the specified barcode value. """
        if barcode == EMPTY_SLOT_SYMBOL or barcode == NOT_FOUND_SLOT_SYMBOL:
            return False

        for b in self.barcodes():
            if b == barcode:
                return True

        return False

    def has_slots_in_common(self, plate_b):
        """ Returns true if the specified plate has any slots with valid barcodes in
        common with this plate.
        """
        plate_a = self
        if plate_a.type != plate_b.type:
            return False

        for i, slot_a in enumerate(plate_a._slots):
            slot_b = plate_b.slot(i+1)
            if slot_a.state() == Slot.VALID:
                if slot_a.barcode_data() == slot_b.barcode_data():
                    return True

        return False

    #########################
    # DRAWING FUNCTIONS
    #########################
    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for slot in self._slots:
            if slot.contains_barcode():
                slot._barcode.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg):
        for i, slot in enumerate(self._slots):
            state = slot.state()
            if state == Slot.UNREADABLE:
                color = Color.Red()
            elif state == Slot.VALID:
                color = Color.Green()
            elif state == Slot.EMPTY:
                color = Color.Grey()
            else:
                color = Color.Red()
            self._geometry.draw_pin_highlight(cvimg, color, i+1)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)


def _find_matching_barcode(slot_bounds, barcodes):
    slot_center, slot_radius = slot_bounds
    slot_sq = slot_radius * slot_radius
    for bc in barcodes:
        barcode_center = bc.bounds()[0]
        if _distance_sq(slot_center, barcode_center) < slot_sq:
            return bc

    return None


def _distance_sq(a, b):
    """ Calculates the square of the distance from a to b.
    """
    x = a[0]-b[0]
    y = a[1]-b[1]
    return x**2+y**2
