import uuid

from .slot import Slot, EMPTY_SLOT_SYMBOL, NOT_FOUND_SLOT_SYMBOL


class Plate:
    """ Represents a sample holder plate.
    """
    def __init__(self, barcodes, geometry, plate_type, frame=1, plate_id=0):
        self.frame = frame
        self.id = plate_id
        self.num_slots = geometry.num_slots
        self.error = geometry.error
        self.type = plate_type
        self._geometry = geometry

        if plate_id == 0:
            self.id = str(uuid.uuid1())

        self.geometry_aligned = geometry.is_aligned()

        # Initialize slots as empty
        self.slots = [Slot(i, None) for i in range(self.num_slots)]

        # If sample holder is aligned, fill appropriate slots with the correct barcodes
        # If alignment failed, just fill slots from the start as no ordering possible.
        if geometry.is_aligned():
            for bc in barcodes:
                center = bc.bounds()[0]
                slot_num = geometry.containing_slot(center)
                self.slots[slot_num-1] = Slot(number=slot_num, barcode=bc)
        else:
            for i, bc in enumerate(barcodes):
                self.slots[i] = Slot(i+1, bc)

        self._sort_slots()

    def _sort_slots(self):
        self.slots.sort(key=lambda slot: slot.number)
        self.num_empty_slots = len([slot for slot in self.slots if slot.state() == Slot.EMPTY])
        self.num_valid_barcodes = len([slot for slot in self.slots if slot.state() == Slot.VALID])

    def barcodes(self):
        """ Returns a list of barcode strings. Empty slots are represented by the empty string.
        """
        return [slot.get_barcode() for slot in self.slots]

    def is_full_valid(self):
        return (self.num_valid_barcodes + self.num_empty_slots) == self.num_slots

    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for slot in self.slots:
            if slot.contains_barcode():
                slot.barcode.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg):
        from dls_barcode import Image
        for i, slot in enumerate(self.slots):
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

    def contains_barcode(self, barcode):
        """ Returns true if the plate contains a slot with the specified barcode value
        """
        if barcode == EMPTY_SLOT_SYMBOL or barcode == NOT_FOUND_SLOT_SYMBOL:
            return False

        for b in self.barcodes():
            if b == barcode:
                return True

        return False

    def has_slots_in_common(self, plateB):
        """ Returns true if the specified plate has any slots with valid barcodes in
        common with this plate.
        """
        plateA = self
        if plateA.type != plateB.type:
            return False

        for i, slotA in enumerate(plateA.slots):
            slotB = plateB.slots[i]
            if slotA.state() == Slot.VALID:
                if slotA.get_barcode() == slotB.get_barcode():
                    return True

        return False

    def merge(self, partial_plate):
        """ Merge this plate with another plate to make a new plate. This is used if
        each plate is from a partially successful scan, i.e., some of the barcodes were
        captured but some were missed. By combining the two plates we can hopefully capture
        every barcode.
        """
        plateB = partial_plate

        # Raise exception if plate type incompatible
        if self.type != plateB.type:
            raise Exception("Cannot merge plate of type '{}' with one of type '{}'".format(self.type, plateB.type))

        slots = []

        # TODO: implement transform function
        # a_to_b_transform = geometry.create_mapping(plateB._geometry)

        # TODO: throw exception if the two barcodes in the same slot do not match
        test_before = max(plateB.num_valid_barcodes, self.num_valid_barcodes)
        for i, slotA in enumerate(self.slots):
            slotB = plateB.slots[i]
            if not slotA.state() == Slot.VALID and slotB.state() == Slot.VALID:
                self.slots[i] = slotB
                # TODO: transform location of B barcode - so that printing of barcodes on image is about right

        self._sort_slots()


