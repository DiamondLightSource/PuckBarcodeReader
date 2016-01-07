
# TODO: detect and report unreadable pins

BAD_DATA_SYMBOL = "XXXXXXX"
EMPTY_SLOT_SYMBOL = ''

class Plate():
    """ Represents a sample holder plate.
    """
    def __init__(self, barcodes, geometry, type):
        self.num_slots = geometry.num_slots
        self.error = geometry.error
        self.barcodes = barcodes
        self.type = type

        self._geometry = geometry

        self.scan_ok = geometry.aligned

        # Get sample pin slot numbers
        for bc in barcodes:
            if geometry.aligned:
                center = bc.bounds[0]
                bc.pinSlot = geometry.closest_slot(center)
            else:
                bc.pinSlot = "NA"

        # Sort barcodes by slot number
        self.barcodes = sorted(barcodes, key=lambda bc: bc.pinSlot)

    def barcodes_string(self):
        """ Returns a string that is a comma-separated list of the barcode values.
        Empty slots are represented by the empty string.
        """
        codes = [EMPTY_SLOT_SYMBOL] * self.num_slots
        for bc in self.barcodes:
            ind = bc.pinSlot - 1
            codes[ind] = bc.data if bc.data is not None else BAD_DATA_SYMBOL

        return ",".join(codes)


    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for bc in self.barcodes:
            bc.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg, color):
        self._geometry.draw_pins(cvimg, color)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)