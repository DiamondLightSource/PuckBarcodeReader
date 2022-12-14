import numpy as np
import cv2

from dls_barcode.scan.with_geometry.slot_scanner import SlotScanner


class BadGeometryException(Exception):
    pass


class PlateScanner:
    BRIGHTNESS_RATIO = 5

    def __init__(self,  plate, single_frame=False):
        self._plate = plate
        self._force_deep_scan = single_frame

    def new_frame(self, frame_img, geometry, barcodes):
        """ Merge the set of barcodes from a new scan into the plate. The new set comes from a new image
        of the same plate, so will almost certainly contain many of the same barcodes. Actually reading a
        barcode is relatively expensive; we iterate through each slot in the plate and only attempt to
        perform a read if we don't already have valid barcode data for the slot.

        For each new frame we update the slot bounds (center, radius) with that calculated by the geometry
        object and update the slot position with the actual position of the center of the barcode. The
        position is likely to be similar to, but not exactly the same as, the bound's center. This info
        is retained as it allows us to properly calculate the geometry for future frames.
        """
        self._frame_img = frame_img
        self._barcodes = barcodes 
        self._plate.set_geometry(geometry)
        
        self.radius_avg = self._calculate_average_radius()
        self.brightness_threshold = self._calculate_brightness_threshold()

        # Fill each slot with the correct barcodes
        for slot in self._plate.slots():
            self._new_slot_frame(slot)

    def _new_slot_frame(self, slot):
        slot.new_frame()

        # Find the barcode from the new set that is in the slot position
        barcode = slot.find_matching_barcode(self._barcodes)
        position = barcode.center() if barcode else slot.bounds().center()
        slot.set_barcode_position(position)
        
        #slot_image = self._slot_image(slot)
        #cv2.imshow("Slot image", slot_image.img)
        #cv2.waitKey(0) 

        slot_scanner = SlotScanner(self._frame_img, slot, barcode, self._force_deep_scan, self.radius_avg, self.brightness_threshold)
        slot_scanner.scan_slot()
    
    def _calculate_average_radius(self):
        if self._barcodes:
            return np.mean([bc.radius() for bc in self._barcodes])
        else:
            return 0

    def _image_contains_point(self, point, radius=0):
        h, w = self._frame_img.img.shape
        return (radius <= point.x <= w - radius - 1) and (radius <= point.y <= h - radius - 1)
    
    def _calculate_brightness_threshold(self):
        """ Calculate the brightness of a small area at each barcode and return the average value.
        A barcode will be much brighter than an empty slot as it usually contains plenty of white
        pixels. This allows us to distinguish between an empty slot with no pin, and a slot with a pin
        where we just haven't been able to locate the barcode.
        """
        pin_brights = []
        for bc in self._barcodes:
            size = bc.radius() / 2
            center_in_frame = self._image_contains_point(bc.center(), radius=size)
            if center_in_frame:
                brightness = self._frame_img.calculate_brightness(bc.center(), size, size)
                pin_brights.append(brightness)

        if any(pin_brights):
            avg_brightness = np.mean(pin_brights)
        else:
            avg_brightness = 0

        return avg_brightness / self.BRIGHTNESS_RATIO

    
