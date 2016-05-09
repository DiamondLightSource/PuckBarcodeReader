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

    def deep_scan(self, slot):
        # Perform more detailed examination of slots for which we don't have results
        slot_num = slot.number()
        center = slot.barcode_position()
        state = slot.state()
        barcode = None

        # If we cant see the slot in the current frame, skip it
        slot_in_frame = self._image_contains_point(center, self.radius_avg/2)
        if not slot_in_frame:
            return barcode

        # ------------- CAREFUL SCANNING ----------------------------
        # If still no result, do a more careful scan for finder patterns and a more careful read
        if state == Slot.NO_RESULT or state == Slot.UNREADABLE:
            slot_img, _ = self.image.sub_image(center, self.radius_avg * 2)

            patterns_deep = list(Locator().locate_datamatrices(slot_img, True, self.radius_avg))
            patterns = list(Locator().locate_datamatrices(slot_img))

            w = 0.25
            wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]

            # If we have a valid looking finder pattern from shallow scan, try to use wiggles to read it
            if len(patterns) > 0:
                # probably don't need to bother with wiggles in continuous mode but perhaps we can keep a count
                # of the number of frames so far and then use wiggles if its taking a while.

                barcode = DataMatrix(patterns[0], slot_img)
                barcode.perform_read(wiggle_offsets)

            # If we have a valid looking finder pattern from the deep scan, try to read it
            elif len(patterns_deep) > 0:
                barcode = DataMatrix(patterns_deep[0], slot_img)
                barcode.perform_read(wiggle_offsets)

        return barcode

    def _calculate_average_radius(self):
        return np.mean([bc.radius() for bc in self.barcodes])

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
    return

    import time
    import os
    dir = "../test-output/bad_barcodes/" + prefix + "/"
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = dir + prefix + "_" + str(time.clock()) + "_slot_" + str(slotnum+1) + ".png"
    image.save_as(filename)

