EMPTY_SLOT_SYMBOL = "----EMPTY----"
NOT_FOUND_SLOT_SYMBOL = '-CANT-FIND-'


class Slot:
    """ Represents a single pin slot in a sample holder.
    """
    NO_RESULT = 0
    EMPTY = 1
    VALID = 2

    def __init__(self, number):
        self._number = number
        self._bounds = None
        self._barcode_position = None
        self._barcode = None
        self._state = self.NO_RESULT

        self._total_frames = 0
        self._barcode_set_this_frame = False

    def new_frame(self):
        """ Call this at the start of a new frame before setting anything. """
        self._total_frames += 1
        self._barcode_set_this_frame = False

    def number(self):
        """ Get the slot number. """
        return self._number

    def bounds(self):
        """ Get the bounds ((x,y), radius) of the slot (as determined by the geometry). """
        return self._bounds

    def barcode(self):
        return self._barcode

    def state(self):
        return self._state
    
    def total_frames(self):
        return self._total_frames

    def barcode_position(self):
        """ Get the position (x,y) of the center of the barcode (not exactly the same as the
        bounds center as predicted by the geometry. """
        return self._barcode_position

    def barcode_this_frame(self):
        """ True if the barcode has been set this frame. """
        return self._barcode_set_this_frame

    def set_bounds(self, bounds):
        self._bounds = bounds

    def set_barcode_position(self, coord):
        self._barcode_position = coord

    def set_barcode(self, barcode):
        if barcode and barcode.is_valid():
            self._barcode = barcode
            self._state = self.VALID
            self._barcode_set_this_frame = True

    def set_empty(self):
        self._barcode = None
        self._state = self.EMPTY

    def set_no_result(self):
        self._barcode = None
        self._state = self.NO_RESULT

    def barcode_data(self):
        """ Gets a string representation of the barcode data; returns an empty
        string if slot is empty
        """
        if self._state == self.EMPTY:
            return EMPTY_SLOT_SYMBOL
        elif self._state == self.VALID:
            return self._barcode.data()
        else:
            return NOT_FOUND_SLOT_SYMBOL

    def find_matching_barcode(self, barcodes):
        for bc in barcodes:
            if self._bounds.contains_point(bc.center()):
                return bc
        return None