from __future__ import division
import logging
from dls_barcode.camera.scanner_message import ScanErrorMessage


from dls_barcode.datamatrix import DataMatrix
from dls_barcode.geometry.unipuck_locator import UnipuckLocator
from dls_barcode.plate import Plate, Slot
from dls_barcode.plate.geometry_adjuster import UnipuckGeometryAdjuster, GeometryAdjustmentError
from dls_barcode.geometry import Geometry, GeometryException
from .empty_detector import EmptySlotDetector
from .plate_scanner import PlateScanner
from ..scan_result import ScanResult
from ..no_barcodes_detected_error import NoBarcodesDetectedError

class GeometryScanner:
    def __init__(self, plate_type, barcode_sizes):
        self.plate_type = plate_type
        self.barcode_sizes = barcode_sizes

        self._frame_number = 0
        self._plate = None
        self._plate_scan = None

        self._frame_img = None
        self._geometry = None
        self._barcodes = []
        self._is_single_image = False
        self._frame_result = None
        self.log = logging.getLogger(".".join([__name__]))

    def scan_next_frame(self, frame, is_single_image=False):
        self._new_frame()

        self._frame_img = frame.convert_to_gray()
        self._is_single_image = is_single_image

        try:
            self._perform_frame_scan()
            self._frame_result.set_plate(self._plate)
            self._frame_result.set_frame(frame)
        #TODO: use logs
        except (NoBarcodesDetectedError, GeometryException, GeometryAdjustmentError) as ex:
            self.log.error(ex)
            self._frame_result.set_error(ScanErrorMessage(str(ex)))
            self._frame_result.set_frame(frame)

        self._frame_result.end_timer()
        return self._frame_result

    def _new_frame(self):
        self._frame_img = None
        self._geometry = None
        self._barcodes = []
        self._is_single_image = False

        self._frame_number += 1

        self._frame_result = ScanResult(self._frame_number)
        self._frame_result.set_previous_plate(self._plate)
        self._frame_result.start_timer()

    def _perform_frame_scan(self):
        self._barcodes = self._locate_all_barcodes_in_image()
        self._frame_result.set_barcodes(self._barcodes)
        if self.plate_type == Geometry.UNIPUCK:
            self._geometry = UnipuckLocator(self._frame_img).find_location() # do something if location not found
        if self._geometry is None:
            self._geometry = self._calculate_geometry()

        self._frame_result.set_geometry(self._geometry)

        # Determine if the previous plate scan has any barcodes in common with this one.
        has_common_barcodes, is_same_align = self._find_common_barcode(self._geometry, self._barcodes)

        if has_common_barcodes and self._plate.is_full_valid():
            return

        elif not has_common_barcodes:
            self._initialize_plate_from_barcodes()

        elif has_common_barcodes and not is_same_align:
            self._geometry = self._adjust_geometry(self._barcodes)

        # Merge with old plate
        if has_common_barcodes:
            self._merge_frame_into_plate()

    def _locate_all_barcodes_in_image(self):
        barcodes = DataMatrix.locate_all_barcodes_in_image_deep(self._frame_img, self.barcode_sizes)
        if len(barcodes) == 0:
            # log = logging.getLogger(".".join([__name__]))
            # log.error(NoBarcodesDetectedError())
            raise NoBarcodesDetectedError()

        return barcodes

    def _calculate_geometry(self):
        slot_centers = [bc.center() for bc in self._barcodes]
        if self.plate_type == Geometry.UNIPUCK:
            use_emptys = len(self._barcodes) < 8
            if use_emptys:
                empty_circles = EmptySlotDetector.detect(self._frame_img, self._barcodes)
                empty_centers = [c.center() for c in empty_circles]
                slot_centers.extend(empty_centers)

        geometry = Geometry.calculate_geometry(self.plate_type, slot_centers)
        return geometry

    def _initialize_plate_from_barcodes(self):
        if self._frame_img is not None:
            self._plate = Plate(self.plate_type)
            self._plate_scan = PlateScanner(self._plate, self._is_single_image)
            self._plate_scan.new_frame(self._frame_img, self._geometry, self._barcodes)

    def _merge_frame_into_plate(self):
        # If one of the barcodes matches the previous frame and is aligned in the same slot, then we can
        # be fairly sure we are dealing with the same plate. Copy all of the barcodes that we read in the
        # previous plate over to their slot in the new plate. Then read any that we haven't already read.
        self._plate_scan.new_frame(self._frame_img, self._geometry, self._barcodes)

    def _find_common_barcode(self, geometry, barcodes):
        """ Determine if the set of finder patterns has any barcodes in common with the existing plate.
        Return a boolean and a list of the barcodes that have been read. """
        has_common_barcodes = False
        has_common_geometry = False
        num_common_barcodes = 0

        # If no plate, don't bother to look for common barcodes
        if self._plate is None:
            return has_common_barcodes, has_common_geometry

        slotted_barcodes = self._make_slotted_barcodes_list(barcodes, geometry)

        # Determine if the previous plate scan has any barcodes in common with this one.
        for i in range(self._plate.num_slots):
            old_slot = self._plate.slot(i)
            new_bc = slotted_barcodes[i-1]

            # Only interested in reading barcodes that might match existing ones
            if new_bc is None or old_slot.state() != Slot.VALID:
                continue

            # Read the barcode
            new_bc.perform_read(self._frame_img)

            if not new_bc.is_valid():
                continue

            num_common_barcodes += 1
            has_common_geometry = new_bc.data() == old_slot.barcode_data()
            has_common_barcodes = has_common_geometry or self._plate.contains_barcode(new_bc.data())

            # If the geometry of this and the previous frame line up, then we are done. Otherwise we
            # need to read at least 2 barcodes so we can perform a realignment.
            if has_common_geometry or num_common_barcodes >= 2:
                break

        return has_common_barcodes, has_common_geometry

    @staticmethod
    def _make_slotted_barcodes_list(barcodes, geometry):
        # Make a list of the unread barcodes with associated slot numbers - from this frame's geometry
        slotted_bcs = [None] * geometry.num_slots()
        for bc in barcodes:
            slot_num = geometry.containing_slot(bc.center())
            if slot_num is not None:
                slotted_bcs[slot_num - 1] = bc

        return slotted_bcs

    def _adjust_geometry(self, barcodes):
        # If we have a barcode that matches with the previous frame but that isn't in the same slot, then
        # at least one of the frames wasn't properly aligned - so we adjust the geometry to match the
        # frames together
        adjuster = UnipuckGeometryAdjuster()
        geometry = adjuster.adjust(self._plate, barcodes)
        return geometry
