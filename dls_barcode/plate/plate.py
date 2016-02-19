
# TODO: check if two barcodes have the same pin slot number

EMPTY_SLOT_SYMBOL = "----EMPTY----"
NOT_FOUND_SLOT_SYMBOL = '-CANT-FIND-'

class Plate():
    """ Represents a sample holder plate.
    """
    def __init__(self, barcodes, geometry, type):
        self.num_slots = geometry.num_slots
        self.error = geometry.error
        self.type = type
        self._geometry = geometry

        self.scan_ok = geometry.is_aligned()

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
                self.slots[i] = Slot(i, bc)

        self._sort_slots()


    def _sort_slots(self):
        self.slots.sort(key=lambda slot: slot.number)
        self.num_empty_slots = len([slot for slot in self.slots if not slot.contains_barcode()])
        self.num_valid_barcodes = len([slot for slot in self.slots if slot.contains_valid_barcode()])

    def barcodes(self):
        """ Returns a list of barcode strings. Empty slots are represented by the empty string.
        """
        return [slot.get_barcode() for slot in self.slots]

    def is_full_valid(self):
        return self.num_valid_barcodes == self.num_slots

    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for slot in self.slots:
            if slot.contains_barcode():
                slot.barcode.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg):
        #self._geometry.draw_pins(cvimg, color)
        from dls_barcode import CvImage
        for i, slot in enumerate(self.slots):
            if slot.contains_unreadable_barcode():
                color = CvImage.ORANGE
            elif slot.contains_valid_barcode():
                color = CvImage.GREEN
            elif slot.is_empty():
                color = CvImage.GREY
            else:
                color = CvImage.RED
            self._geometry.draw_pin_highlight(cvimg, color, i+1)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)

    def has_slots_in_common(self, plateB):
        """ Returns true if the specified plate has any slots with valid barcodes in
        common with this plate.
        """
        plateA = self
        if plateA.type != plateB.type:
            return False

        for i, slotA in enumerate(plateA.slots):
            slotB = plateB.slots[i]
            if slotA.contains_valid_barcode():
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
            if not slotA.contains_valid_barcode() and slotB.contains_valid_barcode():
                self.slots[i] = slotB
                # TODO: transform location of B barcode - so that printing of barcodes on image is about right

        self._sort_slots()


class Slot:
    """ Represents a single pin slot in a sample holder.
    """
    def __init__(self, number, barcode, is_empty=False):
        self.number = number
        self.barcode = barcode
        self._empty = is_empty

    def is_empty(self):
        """ Returns true if it has been detected that the slot is empty (does
        not contain a pin).
        """
        return self._empty

    def contains_barcode(self):
        """ Returns True if the slot contains a pin (regardless of whether
        the barcode is valid)
        """
        return not self.is_empty() and self.barcode is not None

    def contains_valid_barcode(self):
        """ Returns true if the slot contains a pin with a valid barcode
        """
        return self.contains_barcode() and self.barcode.is_valid()

    def contains_unreadable_barcode(self):
        """ Returns true if the slot contains a pin with an unreadable barcode
        """
        return self.contains_barcode() and self.barcode.is_unreadable()

    def get_barcode(self):
        """ Gets a string representation of the barcode dat; returns an empty
        string if slot is empty
        """
        if self.contains_barcode():
            return self.barcode.data()
        elif self.is_empty():
            return EMPTY_SLOT_SYMBOL
        else:
            return NOT_FOUND_SLOT_SYMBOL
