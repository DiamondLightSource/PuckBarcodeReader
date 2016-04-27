import uuid

from .slot import Slot, EMPTY_SLOT_SYMBOL, NOT_FOUND_SLOT_SYMBOL
from dls_barcode.datamatrix import DataMatrix


class BadGeometryException(Exception):
    pass


class Plate:
    """ Represents a sample holder plate.
    """
    def __init__(self, plate_type="Unipuck", num_slots=16):
        self.frame = 0
        self.id = str(uuid.uuid1())

        self.num_slots = num_slots
        self.type = plate_type
        self.error = None
        self._geometry = None

        # Initialize slots
        self._slots = [Slot(i) for i in range(self.num_slots)]
        self._count_slots()

    def _count_slots(self):
        self.num_empty_slots = len([slot for slot in self._slots if slot.state() == Slot.EMPTY])
        self.num_valid_barcodes = len([slot for slot in self._slots if slot.state() == Slot.VALID])

    def merge_barcodes(self, geometry, barcodes):
        """ Merge the set of barcodes from the scan of a new frame into this plate. """
        # If sample holder is aligned, fill appropriate slots with the correct barcodes
        if not geometry.is_aligned:
            raise BadGeometryException("Could not assign barcodes to slots as geometry not aligned.")

        for bc in barcodes:
            center = bc.bounds()[0]
            slot_num = geometry.containing_slot(center)
            self.slot(slot_num).set_barcode(bc)

        self._count_slots()
        self._geometry = geometry
        self.error = geometry.error
        self.frame += 1

    def merge_fps(self, geometry, new_finder_patterns, frame_img):
        """ Merge the set of finder patterns from a new scan into this plate. """
        if not geometry.is_aligned:
            raise BadGeometryException("Could not assign barcodes to slots as geometry not aligned.")

        # Determine the slot numbers of the new finder patterns
        slotted_fps = [None] * geometry.num_slots
        for fp in new_finder_patterns:
            slot_num = geometry.containing_slot(fp.center)
            slotted_fps[slot_num-1] = fp

        # Add in any new barcodes that we are missing
        for i, existing_slot in enumerate(self._slots):
            state = existing_slot.state()
            fp = slotted_fps[i]
            if state != Slot.VALID and fp:
                barcode = DataMatrix(fp, frame_img)
                self.slot(i).set_barcode(barcode)

        self._count_slots()
        self._geometry = geometry
        self.error = geometry.error
        self.frame += 1

    def slot(self, i):
        """ Get the numbered slot on this sample plate."""
        return self._slots[i - 1]

    def barcodes(self):
        """ Returns a list of barcode strings. Empty slots are represented by the empty string.
        """
        return [slot.get_barcode() for slot in self._slots]

    def is_full_valid(self):
        return (self.num_valid_barcodes + self.num_empty_slots) == self.num_slots

    def contains_barcode(self, barcode):
        """ Returns true if the plate contains a slot with the specified barcode value
        """
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
                if slot_a.get_barcode() == slot_b.get_barcode():
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
        from dls_barcode import Image
        for i, slot in enumerate(self._slots):
            state = slot.state()
            if state == Slot.UNREADABLE:
                color = Image.ORANGE
            elif state == Slot.VALID:
                color = Image.GREEN
            elif state == Slot.EMPTY:
                color = Image.GREY
            else:
                color = Image.RED
            self._geometry.draw_pin_highlight(cvimg, color, i+1)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)


