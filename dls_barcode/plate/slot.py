EMPTY_SLOT_SYMBOL = "----EMPTY----"
NOT_FOUND_SLOT_SYMBOL = '-CANT-FIND-'


class Slot:
    """ Represents a single pin slot in a sample holder.
    """
    def __init__(self, number, barcode, is_empty=False):
        self.number = number
        self.barcode = barcode
        self.empty = is_empty

    def is_empty(self):
        """ Returns true if it has been detected that the slot is empty (does
        not contain a pin).
        """
        return self.empty

    def result_not_found(self):
        """ Returns true if we have not yet got a reading from the slot, i.e. we
        haven't seen a barcode, nor confirmed that the slot is empty.
        """
        return not self.is_empty() and not self.contains_barcode()

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