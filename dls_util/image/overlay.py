import time

from dls_util.image import Image, Color
from dls_util.object_with_lifetime import ObjectWithLifetime


class Overlay(ObjectWithLifetime):
    """ Abstract base class. Represents an overlay that can be drawn on top of an image. Has a specified lifetime
    so that the overlay will only be displayed for a short time.
    """
    def __init__(self, lifetime):
        ObjectWithLifetime.__init__(self, lifetime)

    def draw_on_image(self, img):
        pass


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




