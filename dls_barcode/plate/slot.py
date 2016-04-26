EMPTY_SLOT_SYMBOL = "----EMPTY----"
NOT_FOUND_SLOT_SYMBOL = '-CANT-FIND-'


class Slot:
    """ Represents a single pin slot in a sample holder.
    """
    NO_RESULT = 0
    EMPTY = 1
    UNREADABLE = 2
    VALID = 3

    def __init__(self, number, barcode, is_empty=False):
        self.number = number
        self.barcode = barcode
        self.empty = is_empty

    def state(self):
        if self.empty:
            return Slot.EMPTY
        elif self.barcode and self.barcode.is_unreadable():
            return Slot.UNREADABLE
        elif self.barcode and self.barcode.is_valid():
            return Slot.VALID
        else:
            return Slot.NO_RESULT

    def contains_barcode(self):
        state = self.state()
        return state == Slot.UNREADABLE or state == Slot.VALID

    def get_barcode(self):
        """ Gets a string representation of the barcode dat; returns an empty
        string if slot is empty
        """
        if not self.empty and self.barcode is not None:
            return self.barcode.data()
        elif self.empty:
            return EMPTY_SLOT_SYMBOL
        else:
            return NOT_FOUND_SLOT_SYMBOL

