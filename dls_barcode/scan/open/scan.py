from dls_barcode.datamatrix import DataMatrix, Locator


from ..result import ScanResult


class NoBarcodesError(Exception):
    pass


class OpenScanner:
    def __init__(self):
        self._frame_number = 0
        self._frame_img = None

    def scan_frame(self, frame_img):
        self._frame_img = frame_img
        self._frame_number += 1
        result = ScanResult(self._frame_number)
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

        return barcodes

    def _locate_all_barcodes_in_image(self):
        #todo: use deep contour locator
        barcodes = DataMatrix.LocateAllBarcodesInImage(self._frame_img)

        if len(barcodes) == 0:
            raise NoBarcodesError("No Barcodes Detected In Image")

        return barcodes
