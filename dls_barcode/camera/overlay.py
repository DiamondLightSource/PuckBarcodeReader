import time

from util import Image, Color


class Overlay:
    """ Abstract base class. Represents an overlay that can be drawn on top of an image. Has a specified lifetime
    so that the overlay will only be displayed for a short time.
    """
    def __init__(self, lifetime):
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, img):
        pass

    def has_expired(self):
        return (time.time() - self._start_time) > self._lifetime


class TextOverlay(Overlay):
    """ Represents an overlay that can be drawn on top of an image. Used to write status text messages.
    """
    def __init__(self, text, color, lifetime=2):
        Overlay.__init__(self, lifetime)

        self._text = text
        self._color = color
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, img):
        """ Draw the status message to the image.
        """
        image = Image(img)

        # If the overlay has not expired, draw on the plate highlight and/or the status message
        if not self.has_expired():
            image.draw_text(self._text, image.center(), self._color,
                            centered=True, scale=2, thickness=3)


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

