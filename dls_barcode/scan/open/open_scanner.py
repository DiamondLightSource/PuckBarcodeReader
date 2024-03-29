import logging
from dls_barcode.camera.scanner_message import ScanErrorMessage
from dls_barcode.datamatrix import DataMatrix

from dls_barcode.plate import Plate
from dls_barcode.geometry import Geometry
from ..no_barcodes_detected_error import NoBarcodesDetectedError
from .open_scan_result import OpenScanResult


class OpenScanner:
    def __init__(self, barcode_sizes):
        self.plate_type = Geometry.NO_GEOMETRY
        self.barcode_sizes = barcode_sizes

        self._frame_number = 0
        self._frame_img = None
        self._frame = None
        self._is_single_image = False

        self._old_barcode_data = []

    def scan_next_frame(self, frame, is_single_image=False):
        self._frame_img = frame.convert_to_gray()
        self._frame = frame
        self._frame_number += 1
        self._is_single_image = is_single_image
        result = OpenScanResult(self._frame_number)
        result.set_old_barcode_data(self._old_barcode_data)
        result.start_timer()

        # Read all the barcodes in the image
        try:
            barcodes = self._perform_frame_scan()
            result.set_barcodes(barcodes)
            result.set_frame(self._frame)
        except NoBarcodesDetectedError as ex:
            result.set_frame(self._frame)
            result.set_error(ScanErrorMessage(str(ex)))

        # Create a 'blank' geometry object to store the barcode locations
        new_barcodes = result.new_barcodes()
        num_new_barcodes = len(new_barcodes)
        geometry = self._create_geometry(new_barcodes)

        # Create the plate
        if any(new_barcodes):
            plate = Plate(self.plate_type, num_slots=num_new_barcodes)
            plate.set_geometry(geometry)
            for s, barcode in enumerate(new_barcodes):
                plate.slot(s).set_barcode(barcode)
            result.set_plate(plate)

        result.end_timer()
        return result

    def _perform_frame_scan(self):
        barcodes = self._locate_all_barcodes_in_image()

        for barcode in barcodes:
            barcode.perform_read(self._frame_img)

            if self._is_barcode_new(barcode):
                # todo: limit number of previous barcodes stored
                self._old_barcode_data.append(barcode.data())

        return barcodes

    def _create_geometry(self, barcodes):
        """ Create the blank geometry object which just stores the locations of all the barcodes. """
        geometry = Geometry.calculate_geometry(self.plate_type, barcodes)
        return geometry

    def _locate_all_barcodes_in_image(self):
        """ Perform a deep scan to find all the datamatrix barcodes in the image (but don't read them). """
        if self._is_single_image:
            barcodes = DataMatrix.locate_all_barcodes_in_image_deep(self._frame_img, self.barcode_sizes)
        else:
            barcodes = DataMatrix.locate_all_barcodes_in_image(self._frame_img, self.barcode_sizes)
        if len(barcodes) == 0:
            # log = logging.getLogger(".".join([__name__]))
            # log.error(NoBarcodesDetectedError())
            raise NoBarcodesDetectedError()
        return barcodes

    def _is_barcode_new(self, barcode):
        return barcode.is_valid() and barcode.data() not in self._old_barcode_data
