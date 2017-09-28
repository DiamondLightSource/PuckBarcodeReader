from dls_util.image import Overlay, Image, Color


class PlateOverlay(Overlay):
    """ Represents an overlay that can be drawn on top of an image. Used to draw the outline of a plate
    on the continuous scanner camera image to highlight to the user which barcodes on the plate have
    already been scanned.
    """
    def __init__(self, plate, options, lifetime=2):
        Overlay.__init__(self, lifetime)

        self._plate = plate
        self._options = options

    def draw_on_image(self, img):
        """ Draw the plate highlight  to the image.
        """
        image = Image(img)

        # If the overlay has not expired, draw on the plate highlight and/or the status message
        if not self.has_expired():
            self._plate.draw_plate(image, Color.Blue())
            self._plate.draw_pins(image, self._options)