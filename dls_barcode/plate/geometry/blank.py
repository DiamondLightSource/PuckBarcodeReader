from util.shape import Circle


class BlankGeometry:
    _SERIAL_DELIM = "-"

    TYPE_NAME = "None"
    NUM_SLOTS = 20

    def __init__(self, barcodes):
        self._barcode_bounds = []
        self._set_barcode_bounds(barcodes)

    def _set_barcode_bounds(self, barcodes):
        self._barcode_bounds = []
        for barcode in barcodes:
            self._barcode_bounds.append(barcode.bounds())

    def slot_bounds(self, slot_num):
        return self._barcode_bounds[slot_num - 1]

    ############################
    # Serialization
    ############################
    @staticmethod
    def deserialize(string):
        circle_strs = string.split(BlankGeometry._SERIAL_DELIM)

        barcode_bounds = []
        for string in circle_strs:
            circle = Circle.deserialize(string)
            barcode_bounds.append(circle)

        geo = BlankGeometry([])
        geo._barcode_bounds = barcode_bounds
        return geo

    def serialize(self):
        circles = []
        for bounds in self._barcode_bounds:
            circles.append(bounds.serialize())
        return self._SERIAL_DELIM.join(circles)
