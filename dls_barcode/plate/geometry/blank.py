class BlankGeometry:
    TYPE_NAME = "None"
    NUM_SLOTS = 20

    def __init__(self, barcodes):
        self._slot_bounds = []
        self._set_slot_bounds(barcodes)

    def _set_slot_bounds(self, barcodes):
        self._slot_bounds = []
        for barcode in barcodes:
            self._slot_bounds.append(barcode.bounds())

    def slot_bounds(self, slot_num):
        return self._slot_bounds[slot_num - 1]
