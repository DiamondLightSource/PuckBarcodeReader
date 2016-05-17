import numpy as np

from .slot import Slot
from dls_barcode.datamatrix import DataMatrix, Locator


class SlotScanner:
    BRIGHTNESS_RATIO = 5

    def __init__(self, image, barcodes):
        self.image = image
        self.barcodes = barcodes

        self.radius_avg = self._calculate_average_radius()
        self.brightness_threshold = None

    def is_slot_empty(self, slot):
        if self.brightness_threshold is None:
            self.brightness_threshold = self._calculate_brightness_threshold()

        center = slot.barcode_position()

        # If we cant see the slot in the current frame, skip it
        slot_in_frame = self._image_contains_point(center, self.radius_avg/2)
        if not slot_in_frame:
            return False

        brightness = self.image.calculate_brightness(center, self.radius_avg / 2)
        return brightness < self.brightness_threshold

    def wiggles_read(self, barcode):
        w = 0.25
        wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]
        barcode.perform_read(wiggle_offsets)

        return barcode

    def deep_scan(self, slot):
        # Perform more detailed examination of slots for which we don't have results
        slot_num = slot.number()
        center = slot.barcode_position()
        state = slot.state()
        barcodes = []

        # If we cant see the slot in the current frame, skip it
        slot_in_frame = self._image_contains_point(center, self.radius_avg/2)
        if not slot_in_frame:
            return []

        if state == Slot.NO_RESULT or state == Slot.UNREADABLE:
            slot_img, _ = self.image.sub_image(center, self.radius_avg * 2)

            fps = list(Locator().locate_datamatrices(slot_img, True, self.radius_avg))

            if len(fps) > 0:

                if len(fps) > 1:
                    from dls_barcode.util import Image
                    # print("DEEP PATTERNS = " + str(len(fps)))
                    color = slot_img.to_alpha()
                    for fp in fps:
                        fp.draw_to_image(color, Image.random_color())
                    DEBUG_SAVE_IMAGE(color, "double deep fps", slot_num)

            barcodes = [DataMatrix(fp, slot_img) for fp in fps]

        return barcodes

    def _calculate_average_radius(self):
        if self.barcodes:
            return np.mean([bc.radius() for bc in self.barcodes])
        else:
            return 0

    def _calculate_brightness_threshold(self):
        """ Calculate the brightness of a small area at each barcode and return the average value.
        A barcode will be much brighter than an empty slot as it usually contains plenty of white
        pixels. This allows us to distinguish between an empty slot with no pin, and a slot with a pin
        where we just haven't been able to locate the barcode.
        """
        pin_brights = []
        for bc in self.barcodes:
            center_in_frame = self._image_contains_point(bc.center(), radius=bc.radius()/2)
            if center_in_frame:
                brightness = self.image.calculate_brightness(bc.center(), bc.radius() / 2)
                pin_brights.append(brightness)

        if any(pin_brights):
            avg_brightness = np.mean(pin_brights)
        else:
            avg_brightness = 0

        return avg_brightness / self.BRIGHTNESS_RATIO

    def _image_contains_point(self, point, radius=0):
        h, w = self.image.img.shape
        x, y = point
        return (radius <= x <= w - radius - 1) and (radius <= y <= h - radius - 1)


def DEBUG_SAVE_IMAGE(image, prefix, slotnum):

    import time
    import os
    dir = "../test-output/bad_barcodes/" + prefix + "/"
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = dir + prefix + "_" + str(time.clock()) + "_slot_" + str(slotnum+1) + ".png"
    image.save_as(filename)

