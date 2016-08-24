from ..result import ScanResult


class OpenScanResult(ScanResult):
    def __init__(self, frame_number):
        ScanResult.__init__(self, frame_number)

        self._old_barcode_data = []

    def success(self):
        return self._error is None

    def new_barcodes(self):
        new = []
        for barcode in self._barcodes:
            if barcode.is_valid() and barcode.data() not in self._old_barcode_data:
                    new.append(barcode)

        return new

    def set_old_barcode_data(self, barcode_data):
        self._old_barcode_data = barcode_data[:]

    def any_new_barcodes(self):
        return len(self.new_barcodes()) > 0

    def print_summary(self):
        print('\n------- Frame {} -------'.format(self._frame_number))
        print("Scan Duration: {0:.3f} secs".format(self.scan_time()))
