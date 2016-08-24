import time


class OpenScanResult:
    def __init__(self):
        self._barcodes = []
        self._error = None

        self._start_time = 0
        self._scan_time = 0

    def start_timer(self):
        self._start_time = time.time()

    def end_timer(self):
        self._scan_time = time.time() - self._start_time

    ############################
    # Accessors
    ############################
    def barcodes(self): return self._barcodes

    def error(self): return self._error

    def set_barcodes(self, value): self._barcodes = value
    
    def set_error(self, value): self._error = value
