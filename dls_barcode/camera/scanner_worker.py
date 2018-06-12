import time

from dls_util.image import Image
from dls_util import Beeper
from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_barcode.datamatrix import DataMatrix
from .camera_position import CameraPosition
from .plate_overlay import PlateOverlay
from .scanner_message import NoNewBarcodeMessage, ScanErrorMessage

NO_PUCK_TIME = 2


class ScannerWorker:
    """ Scan images for barcodes, combining partial scans until a full puck is reached.
    Keep the record of the last scan which was at least partially successful (aligned geometry
    and some barcodes scanned). For each new frame, we can attempt to merge the results with
    this previous plates so that we don't have to re-read any of the previously captured barcodes
    (because this is a relatively expensive operation).
    """
    def run(self, task_queue, overlay_queue, result_queue, message_queue, kill_queue, config, cam_position):
        print("SCANNER start")
        self._last_puck_time = time.time()

        SlotScanner.DEBUG = config.slot_images.value()
        SlotScanner.DEBUG_DIR = config.slot_image_directory.value()

        self._create_scanner(cam_position, config)

        display = True
        while kill_queue.empty():
            if display:
                print("--- scanner inside loop")
                display = False

            if task_queue.empty():
                continue

            frame = task_queue.get(True)
            self._process_frame(frame, config, overlay_queue, result_queue, message_queue)

        print("SCANNER stop & kill")

    def _process_frame(self, frame, config, overlay_queue, result_queue, message_queue):
        image = Image(frame)
        gray_image = image.to_grayscale()

        # If we have an existing partial plate, merge the new plate with it and only try to read the
        # barcodes which haven't already been read. This significantly increases efficiency because
        # barcode read is expensive.
        scan_result = self._scanner.scan_next_frame(gray_image)

        if config.console_frame.value():
            scan_result.print_summary()

        if scan_result.success():
            # Record the time so we can see how long its been since we last saw a puck
            self._last_puck_time = time.time()

            plate = scan_result.plate()
            if scan_result.any_valid_barcodes():
                overlay_queue.put(PlateOverlay(plate, config))
                self._plate_beep(plate, config.scan_beep.value())

            if scan_result.any_new_barcodes():
                result_queue.put((plate, image))
        elif scan_result.any_valid_barcodes():
            # We have read valid barcodes but they are not new, so the scanner didn't even output a plate
            self._last_puck_time = time.time()
            message_queue.put(NoNewBarcodeMessage()) #important used in the message logic
        elif scan_result.error() is not None and (time.time() - self._last_puck_time > NO_PUCK_TIME):
            #TODO use log
            message_queue.put(ScanErrorMessage(scan_result.error()))

    def _create_scanner(self, cam_position, config):
        if cam_position == CameraPosition.SIDE:
            plate_type = "None"
            barcode_sizes = DataMatrix.DEFAULT_SIDE_SIZES
        else:
            plate_type = config.plate_type.value()
            barcode_sizes = [config.top_barcode_size.value()]

        if plate_type == "None":
            self._scanner = OpenScanner(barcode_sizes)
        else:
            self._scanner = GeometryScanner(plate_type, barcode_sizes)

    def _plate_beep(self, plate, do_beep):
        if not do_beep:
            return

        empty_fraction = (plate.num_slots - plate.num_valid_barcodes()) / plate.num_slots
        frequency = int(10000 * empty_fraction + 37)
        duration = 200
        Beeper.beep(frequency, duration)