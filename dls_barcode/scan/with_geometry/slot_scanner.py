from __future__ import division

import logging
import math

from dls_barcode.plate.slot import Slot


class SlotScanner:
    FRAMES_BEFORE_DEEP = 3
    
    def __init__(self, image, slot, barcode, radius_avg, brightness_threshold):
        self._log = logging.getLogger(".".join([__name__]))

        self.image = image
        self.slot = slot
        self.barcode = barcode

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

    def _should_do_deep_scan(self):
        return self.slot.total_frames >= self.FRAMES_BEFORE_DEEP