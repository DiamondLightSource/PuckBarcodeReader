import time

from util import Image, Color


class Overlay:
    """ Abstract base class. Represents an overlay that can be drawn on top of an image. Has a specified lifetime
    so that the overlay will only be displayed for a short time.
    """
    def __init__(self, lifetime):
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, image):
        pass

    def has_expired(self):
        return (time.time() - self._start_time) > self._lifetime


class TextOverlay(Overlay):
    """ Represents an overlay that can be drawn on top of an image. Used to write status text messages.
    """
    def __init__(self, text, options, lifetime=2):
        Overlay.__init__(self, lifetime)

        self._text = text
        self._options = options
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, image):
        """ Draw the status message to the image.
        """
        cv_image = Image(image)

        # If the overlay has not expired, draw on the plate highlight and/or the status message
        if not self.has_expired():
            color_ok = self._options.col_ok()
            cv_image.draw_text(self._text, cv_image.center(), color_ok, centered=True, scale=4, thickness=3)


class PlateOverlay(Overlay):
    """ Represents an overlay that can be drawn on top of an image. Used to draw the outline of a plate
    on the continuous scanner camera image to highlight to the user which barcodes on the plate have
    already been scanned.
    """
    def __init__(self, plate, options, lifetime=2):
        self._plate = plate
        self._options = options
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, image):
        """ Draw the plate highlight  to the image.
        """
        cv_image = Image(image)

        # If the overlay has not expired, draw on the plate highlight and/or the status message
        if not self.has_expired():
            self._plate.draw_plate(cv_image, Color.Blue())
            self._plate.draw_pins(cv_image, self._options)

