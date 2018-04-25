import cv2

class ImageMorphology:
    """
    Basic morphological operations called with default rectangular shape of the structural element.
    """

    def __init__(self, image):
        self.image = image

    def do_dilate_morph(self, morph_size):
        """ Perform a dilate operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        dil = cv2.morphologyEx(self.image, cv2.MORPH_DILATE, element, iterations=1)
        return dil

    def do_erode_morph(self, morph_size):
        """ Perform an erode operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        ero = cv2.morphologyEx(self.image, cv2.MORPH_ERODE, element, iterations=1)
        return ero

    def do_close_morph(self, morph_size):
        """ Perform a close operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(self.image, cv2.MORPH_CLOSE, element, iterations=1)
        return closed

    def do_open_morph(self, morph_size):
        """ Perform an open operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        opened = cv2.morphologyEx(self.image, cv2.MORPH_OPEN, element, iterations=1)
        return opened