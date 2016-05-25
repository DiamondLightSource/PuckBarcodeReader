from __future__ import division

import numpy as np
import math
import time
import os

from .slot import Slot
from dls_barcode.datamatrix import DataMatrix, Locator
from dls_barcode.util import Image


class SlotScanner:
    BRIGHTNESS_RATIO = 5
    DEBUG_MODE = True

    def __init__(self, image, barcodes, options):
        self.image = image
        self.barcodes = barcodes
        self._options = options

        self.radius_avg = self._calculate_average_radius()
        self.side_avg = self.radius_avg * (2 / math.sqrt(2))
        self.brightness_threshold = None

    def is_slot_empty(self, slot):
        if self.brightness_threshold is None:
            self.brightness_threshold = self._calculate_brightness_threshold()

        center = slot.barcode_position()

        # If we cant see the slot in the current frame, skip it
        slot_in_frame = self._image_contains_point(center, self.radius_avg/2)
        if not slot_in_frame:
            return False

        size = self.radius_avg / 2
        brightness = self.image.calculate_brightness(center, size, size)
        return brightness < self.brightness_threshold

    def wiggles_read(self, barcode, locate_type="NORMAL"):
        w = 0.25
        wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]
        barcode.perform_read(wiggle_offsets)

        self._DEBUG_WIGGLES_READ(barcode, locate_type, self.side_avg)

        return barcode

    def deep_scan(self, slot):
        if not self._is_slot_worth_scanning(slot):
            return []

        img = self._slot_image(slot)
        fps = list(Locator().locate_deep(img, self.radius_avg))
        barcodes = [DataMatrix(fp, img) for fp in fps]

        self._DEBUG_MULTI_FP_IMAGE(img, fps, slot.number())

        return barcodes

    def square_scan(self, slot):
        if not self._is_slot_worth_scanning(slot):
            return None

        img = self._slot_image(slot)
        fp = Locator().locate_square(img, self.side_avg)

        self._DEBUG_SQUARE_LOCATOR(img, fp, slot.number())

        return DataMatrix(fp, img)

    def _is_slot_worth_scanning(self, slot):
        state = slot.state()
        center = slot.barcode_position()

        # If we cant see the slot in the current frame, skip it
        slot_in_frame = self._image_contains_point(center, self.radius_avg/2)
        if not slot_in_frame:
            return False

        if state == Slot.VALID or state == Slot.EMPTY:
            return False

        return True

    def _slot_image(self, slot):
        center = slot.barcode_position()
        slot_img, _ = self.image.sub_image(center, self.radius_avg * 2)
        return slot_img

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
            size = bc.radius() / 2
            center_in_frame = self._image_contains_point(bc.center(), radius=size)
            if center_in_frame:
                brightness = self.image.calculate_brightness(bc.center(), size, size)
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

    def _DEBUG_WIGGLES_READ(self, barcode, locate_type, side_length):
        if not self._options.slot_images:
            return

        if barcode.is_valid():
            print("DEBUG - WIGGLES SUCCESSFUL - " + locate_type)
            result = "_SUCCESS"
        else:
            result = "_FAIL"

        slot_img = Image(None, barcode._image).to_alpha()

        self._DEBUG_SAVE_IMAGE(slot_img, locate_type + result, side_length - 1)

        fp = barcode._finder_pattern
        fp.draw_to_image(slot_img, Image.GREEN)

        self._DEBUG_SAVE_IMAGE(slot_img, locate_type + result, side_length - 1)

    def _DEBUG_MULTI_FP_IMAGE(self, slot_img, fps, slot_num):
        if not self._options.slot_images:
            return

        if len(fps) > 1:
            color = slot_img.to_alpha()
            for fp in fps:
                fp.draw_to_image(color, Image.random_color())
            self._DEBUG_SAVE_IMAGE(color, "DEEP CONTOUR ALL FPS", slot_num)

    def _DEBUG_SQUARE_LOCATOR(self, slot_img, fp, slot_num):
        if not self._options.slot_images:
            return

        color = slot_img.to_alpha()
        fp.draw_to_image(color, Image.GREEN)
        self._DEBUG_SAVE_IMAGE(color, "SQUARE LOCATOR FP", slot_num)

    def _DEBUG_SAVE_IMAGE(self, image, prefix, slotnum):
        if not self._options.slot_images:
            return

        dir = self._options.slot_image_directory + prefix + "/"
        if not os.path.exists(dir):
            os.makedirs(dir)
        filename = dir + prefix + "_" + str(time.time()) + "_slot_" + str(slotnum+1) + ".png"
        image.save_as(filename)

