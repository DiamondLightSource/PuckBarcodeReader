from dls_barcode.datamatrix import DataMatrix, Locator


from .result import OpenScanResult


class NoBarcodesError(Exception):
    pass


class OpenScanner:
    def __init__(self):
        self._frame_number = 0
        self._frame_img = None

        self._old_barcode_data = []

    def scan_frame(self, frame_img):
        self._frame_img = frame_img
        self._frame_number += 1
        result = OpenScanResult(self._frame_number)
        result.set_old_barcode_data(self._old_barcode_data)
        result.start_timer()

        try:
            barcodes = self._perform_frame_scan()
            result.set_barcodes(barcodes)

        except NoBarcodesError as ex:
            result.set_error(str(ex))

        result.end_timer()
        return result

    def _perform_frame_scan(self):
        barcodes = self._locate_all_barcodes_in_image()

        for barcode in barcodes:
            barcode.perform_read(DataMatrix.DIAG_WIGGLES)

            if self._is_barcode_new(barcode):
                # todo: limit number of previous barcodes stored
                self._old_barcode_data.append(barcode.data())

        return barcodes

    def _locate_all_barcodes_in_image(self):
        # todo: use deep contour locator
        barcodes = DataMatrix.LocateAllBarcodesInImage(self._frame_img)
        if len(barcodes) == 0:
            raise NoBarcodesError("No Barcodes Detected In Image")
        return barcodes

    def _is_barcode_new(self, barcode):
        return barcode.is_valid() and barcode.data() not in self._old_barcode_data
