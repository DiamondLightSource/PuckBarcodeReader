
#ToDo: detect and report unreadable pins

class Plate():
    """ Represents a sample holder plate.
    """
    def __init__(self, barcodes, geometry):
        self.num_slots = geometry.num_slots
        self.error = geometry.error
        self.barcodes = barcodes

        self._geometry = geometry

        # Get sample pin slot numbers
        for bc in barcodes:
            center = bc.bounds[0]
            bc.pinSlot = geometry.closest_slot(center)

        # Sort barcodes by slot number
        self.barcodes = sorted(barcodes, key=lambda bc: bc.pinSlot)


    def draw_barcodes(self, cvimg, ok_color, bad_color):
        for bc in self.barcodes:
            bc.draw(cvimg, ok_color, bad_color)

    def draw_plate(self, cvimg, color):
        self._geometry.draw_plate(cvimg, color)

    def draw_pins(self, cvimg, color):
        self._geometry.draw_pins(cvimg, color)

    def crop_image(self, cvimg):
        self._geometry.crop_image(cvimg)