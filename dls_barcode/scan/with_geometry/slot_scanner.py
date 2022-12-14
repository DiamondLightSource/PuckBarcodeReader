from __future__ import division

import logging
import math

from dls_barcode.datamatrix import DataMatrix, Locator
from dls_barcode.plate.slot import Slot


class SlotScanner:
    FRAMES_BEFORE_DEEP = 3
    
    def __init__(self, image, slot, barcode, force_deep_scan, radius_avg, brightness_threshold):
        self._log = logging.getLogger(".".join([__name__]))

        self.image = image
        self.slot = slot
        self.barcode = barcode
        self._force_deep_scan = force_deep_scan

        self.radius_avg = radius_avg
        self.side_avg = self.radius_avg * (2 / math.sqrt(2))
        self.brightness_threshold = brightness_threshold

    def is_slot_empty(self):
        center = self.slot.barcode_position()

        # If we cant see the slot in the current frame, skip it
        #slot_in_frame = self._image_contains_point(center, self.radius_avg / 2)
        #if not slot_in_frame:
        #    return False

        size = self.radius_avg / 2
        brightness = self.image.calculate_brightness(center, size, size)
        return brightness < self.brightness_threshold

    def scan_slot(self):
        if self.slot.state() != Slot.VALID and self.barcode:
            self.barcode.perform_read(self.image)
            self.slot.set_barcode(self.barcode)
        # If the slot barcode has already been read correctly, skip it
        if self.slot.state() == Slot.VALID:
            return

        # Check for empty slot
        if self.is_slot_empty():
            self.slot.set_empty()
            return

        # Clear any previous (empty/unread) result
        self.slot.set_no_result()

        #if self._should_do_deep_scan():
        #    self._perform_deep_contour_slot_scan()
        #    self._perform_square_slot_scan()

    def _should_do_deep_scan(self):
        return self._force_deep_scan or self.slot.total_frames >= self.FRAMES_BEFORE_DEEP
    
    def _perform_deep_contour_slot_scan(self):
        if self.slot.state() != Slot.VALID:
            barcode = self.deep_scan()
            if not self._force_deep_scan and barcode:
                barcode.perform_read(self.image)
                self.slot.set_barcode(barcode)

    def _perform_square_slot_scan(self):
        if self.slot.state() != Slot.VALID:
            barcode = self.square_scan()
            if barcode is not None:
                barcode.perform_read(self.image)
                self.slot.set_barcode(barcode)

    def deep_scan(self):
        if not self._is_slot_worth_scanning():
            return []

        img = self._slot_image()
        fps = list(Locator().locate_deep(img, self.radius_avg))
        barcodes = [DataMatrix(fp) for fp in fps]

        return barcodes

    def square_scan(self):
        if not self._is_slot_worth_scanning():
            return None

        img = self._slot_image()
        fp = Locator().locate_square(img, self.side_avg)

        barcode = None
        if fp is not None:
            barcode = DataMatrix(fp)

        return barcode
    
    def _slot_image(self):
        center = self.slot.barcode_position()
        slot_img, _ = self.image.sub_image(center, self.radius_avg * 2)
        return slot_img

    def _is_slot_worth_scanning(self):
        state = self.slot.state()
       # center = self.slot.barcode_position()

        # If we cant see the slot in the current frame, skip it
        #slot_in_frame = self._image_contains_point(center, self.radius_avg / 2) ### ?????
        #if not slot_in_frame:
        #    return False

        if state == Slot.VALID or state == Slot.EMPTY:
            return False

        return True

   