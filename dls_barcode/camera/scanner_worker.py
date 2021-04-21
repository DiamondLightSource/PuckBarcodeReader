import logging
import time


from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_barcode.datamatrix import DataMatrix
from .camera_position import CameraPosition
from .frame_processor import FrameProcessor
from .result_processor import ResultPorcessor

from .scanner_message import NoNewBarcodeMessage, ScanErrorMessage, NoNewPuckBarcodeMessage

NO_PUCK_TIME = 2


class ScannerWorker:
    """ Scan images for barcodes, combining partial scans until a full puck is reached.
    Keep the record of the last scan which was at least partially successful (aligned geometry
    and some barcodes scanned). For each new frame, we can attempt to merge the results with
    this previous plates so that we don't have to re-read any of the previously captured barcodes
    (because this is a relatively expensive operation).
    """
    def __init__(self):
        self._log = logging.getLogger(".".join([__name__]))

    def run(self, task_queue, overlay_queue, result_queue, message_queue, kill_queue, config, cam_position):
        self._log.debug("SCANNER start")
        self._last_puck_time = time.time()

        SlotScanner.DEBUG = config.slot_images.value()
        SlotScanner.DEBUG_DIR = config.slot_image_directory.value()

        self._create_scanner(cam_position, config)

        display = True
        while kill_queue.empty():
            if display:
                self._log.debug("--- scanner inside loop")
                display = False

            if task_queue.empty():
                continue

            frame = task_queue.get(True)
            self._process_frame(frame, config, overlay_queue, result_queue, message_queue)

        self._log.debug("SCANNER stop & kill")

    def _process_frame(self, frame, config, overlay_queue, result_queue, message_queue):

        frame_processor = FrameProcessor(frame, self._scanner)
        frame_processor.convert_to_gray()
        scan_result = frame_processor.scan_frame()

        result_porcessor = ResultPorcessor(scan_result, config)

        result_porcessor.print_summary()

        if result_porcessor.result_success():
            self._last_puck_time = time.time()
            result_porcessor.set_result_palte()
            if result_porcessor.result_has_any_valid_barcodes():
                o = result_porcessor.get_overlay()
                overlay_queue.put(o)
            if result_porcessor.result_has_any_new_barcode():
                r = (result_porcessor.get_plate(), frame_processor.get_image())
                result_queue.put(r)

        elif result_porcessor.result_has_any_valid_barcodes():
            self._last_puck_time = time.time()
            m = result_porcessor.get_message()
            message_queue.put(m)

        elif result_porcessor.result_error and (time.time() - self._last_puck_time > NO_PUCK_TIME):
            m = ScanErrorMessage(result_porcessor.get_result_error())
            message_queue.put(m)

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
