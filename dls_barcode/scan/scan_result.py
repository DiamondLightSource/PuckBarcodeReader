import logging
import time


class ScanResult:
    def __init__(self, frame_number):
        self._log = logging.getLogger(".".join([__name__]))

        self._frame_number = frame_number

        self._previous_plate = None
        self._previous_plate_count = False

        self._barcodes = []
        self._geometry = None
        self._plate = None
        self._error = None
        self._frame = None

        self._start_time = 0
        self._scan_time = 0

    def start_timer(self):
        self._start_time = time.time()

    def end_timer(self):
        self._scan_time = time.time() - self._start_time

    def set_previous_plate(self, plate):
        self._previous_plate = plate
        self._previous_plate_count = plate.num_valid_barcodes() if plate else 0

    ############################
    # Accessors
    ############################
    def frame_number(self):
        return self._frame_number

    def barcodes(self):
        return self._barcodes
    
    def get_first_barcode(self):
        return self._barcodes[0]
    
    def has_valid_barcodes(self):
        if len(self._barcodes) > 0:
            if self._barcodes[0].data() != '':
                return True
            
        return False

    def geometry(self):
        return self._geometry

    def plate(self):
        return self._plate

    def error(self):
        return self._error

    def set_barcodes(self, value):
        self._barcodes = value

    def set_geometry(self, value):
        self._geometry = value

    def set_plate(self, value):
        self._plate = value

    def set_error(self, value):
        self._error = value
        
    def set_frame(self, frame):
        self._frame = frame
        
    def get_frame(self):
        return self._frame

    def get_frame_image(self):
        if self._frame is not None :
            return self._frame.get_image()
        else:
            return self._frame
    
    ############################
    # Status Functions
    ############################
    def success(self):
        return self._plate is not None and self._error is None

    def is_aligned(self):
        return self._geometry is not None

    def any_finder_patterns(self):
        return any(self._barcodes)

    def any_valid_barcodes(self):
        return any([bc.is_read() and bc.is_valid() for bc in self._barcodes])

    def is_full_valid(self):
        return self._plate is not None and self._plate.is_full_valid()

    def scan_time(self):
        return self._scan_time

    def is_new_plate(self):
        return self._plate and \
               (self._previous_plate is None or self._plate.id != self._previous_plate.id)

    def any_new_barcodes(self):
        return self.is_new_plate() or \
               (self._plate.num_valid_barcodes() != self._previous_plate_count)

    def already_scanned(self):
        return self.is_full_valid() and not self.any_new_barcodes()

    def print_summary(self):
        self._log.debug('Frame {}'.format(self._frame_number))
        self._log.debug("Scan Duration: {0:.3f} secs".format(self.scan_time()))

        if self.any_finder_patterns():
            self._log.debug("Barcodes Located: {}".format(len(self._barcodes)))

        if self.is_aligned():
            self._log.debug("Geometry - {}".format(self._geometry.to_string()))

        if self._plate:
            plate = self._plate
            self._log.debug("Plate:")

            status = "(new plate)" if self.is_new_plate() else ""
            self._log.debug("* Plate ID: {} {}".format(plate.id, status))

            self._log.debug("* Slots: {} read; {} empty; {} unread".format(
                plate.num_valid_barcodes(), plate.num_empty_slots(), plate.num_unread_barcodes()))

            new_reads = self._plate.num_valid_barcodes()
            if not self.is_new_plate():
                new_reads -= self._previous_plate_count
            self._log.debug("* New Barcodes: {}".format(new_reads))

            self._log.debug("* Scan Complete: {}".format(str(self.is_full_valid())))

        if not self.success():
            self._log.debug("Error: {}".format(self._error))
