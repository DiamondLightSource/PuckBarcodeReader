import time

from util import Image, Color


class Overlay:
    """ Represents an overlay that can be drawn on top of an image. Used to draw the outline of a plate
    on the continuous scanner camera image to highlight to the user which barcodes on th plate have
    already been scanned. Also writes status text messages. Has a specified lifetime so that the overlay
    will only be displayed for a short time.
    """
    def __init__(self, plate, options, text=None, lifetime=2):
        self._plate = plate
        self._options = options
        self._text = text
        self._lifetime = lifetime
        self._start_time = time.time()

    def draw_on_image(self, image):
        """ Draw the plate highlight and status message to the image as well as a message that tells the
        user how to close the continuous scanning window.
        """
        cv_image = Image(image)

        # If the overlay has not expired, draw on the plate highlight and/or the status message
        if (time.time() - self._start_time) < self._lifetime:
            if self._plate is not None:
                self._plate.draw_plate(cv_image, Color.Blue())
                self._plate.draw_pins(cv_image, self._options)

            if self._text is not None:
                color_ok = self._options.col_ok()
                cv_image.draw_text(self._text, cv_image.center(), color_ok, centered=True, scale=4, thickness=3)
