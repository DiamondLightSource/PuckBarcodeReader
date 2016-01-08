
# TODO: detect and report unreadable pins
# TODO: check if two barcodes have the same pin slot number

BAD_DATA_SYMBOL = "XXXXXXX"
EMPTY_SLOT_SYMBOL = ''

class Plate():
    """ Represents a sample holder plate.
    """
    def __init__(self, barcodes, geometry, type):
        self.num_slots = geometry.num_slots
        self.error = geometry.error
        self.type = type
        self._geometry = geometry

        self.scan_ok = geometry.aligned

        # Initialize slots as empty
        self.slots = [Slot(i, None) for i in range(self.num_slots)]

        # If sample holder is aligned, fill appropriate slots with the correct barcodes
        # If alignment failed, just fill slots from the start as no ordering possible.
        if geometry.aligned:
            for bc in barcodes:
                center = bc.bounds[0]
                slot_num = geometry.closest_slot(center)
                bc.pinSlot = slot_num
                self.slots[slot_num-1] = Slot(number=slot_num, barcode=bc)
        else:
            for i, bc in enumerate(barcodes):
                bc.pinSlot = "NA"
                self.slots[i] = Slot(i, bc)

    def barcodes_string(self):
        """ Returns a string that is a comma-separated list of the barcode values.
        Empty slots are represented by the empty string.
        """
        codes = [slot.get_barcode() for slot in self.slots]
        return ",".join(codes)


    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for slot in self.slots:
            if slot.contains_pin():
                slot.barcode.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg, color):
        self._geometry.draw_pins(cvimg, color)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)


class Slot:
    """ Represents a single pin slot in a sample holder.
    """
    def __init__(self, number, barcode):
        self.number = number
        self.barcode = barcode

    def contains_pin(self):
        """ Returns True if the slot contains a pin (regardless of whether
        the barcode is valid)
        """
        return self.barcode is not None

    def contains_valid_barcode(self):
        """ Returns true if the slot contains a pin with a valid barcode
        """
        return self.contains_pin() \
               and self.barcode.data != EMPTY_SLOT_SYMBOL \
               and self.barcode.data != BAD_DATA_SYMBOL

    def get_barcode(self):
        """ Gets a string representation of the barcode dat; returns an empty
        string if slot is empty
        """
        if self.contains_pin():
            return self.barcode.data
        else:
            return EMPTY_SLOT_SYMBOL
