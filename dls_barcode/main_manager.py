import logging
import multiprocessing
import queue
import time

from PyQt5 import QtCore

from dls_barcode.camera import CameraScanner, CameraSwitch, ScanErrorMessage, NoNewPuckBarcodeMessage
from dls_barcode.camera.scanner_message import CameraErrorMessage

from dls_util import Beeper
from dls_util.cv.camera import Camera
from dls_util.cv.capture_manager import CaptureManager
from dls_util.logging.process_logging import configure_new_process, ProcessLogger

RESULT_TIMER_PERIOD = 1000  # ms
VIEW_TIMER_PERIOD = 1  # ms
MESSAGE_TIMER_PERIOD = 1  # ms


class MainManager:

    def __init__(self, ui, config, process_logger):

        self._ui = ui
        self._config = config

        # Scan elements
        self._camera_scanner = None
        self._camera_switch = None
        self._scan_completed_message_flag = False

        # Set the logger
        self._process_logger = process_logger
        self._log = logging.getLogger(".".join([__name__]))

        # Queue that holds new results generated in continuous scanning mode
        self._result_queue = multiprocessing.Queue()
        self._view_queue = multiprocessing.Queue()
        self._message_queue = multiprocessing.Queue()
        # initialise all actions
        self._ui.set_actions_triger(self._cleanup, self._cleanup_logging,
            self.initialise_scanner, self._camera_capture_alive)
        # breaks the cameras - need something better
        #e = self.test_cameras()
        #if e is not None:
        #    self._ui.displayCameraErrorMessage(e)


    def initialise_timers(self):
        # Timer that controls how often new scan results are looked for
        self._result_timer = QtCore.QTimer()
        self._result_timer.timeout.connect(self._read_result_queue)
        self._result_timer.start(RESULT_TIMER_PERIOD)

        self._view_timer = QtCore.QTimer()
        self._view_timer.timeout.connect(self._read_view_queue)
        self._view_timer.start(VIEW_TIMER_PERIOD)

        self._message_timer = QtCore.QTimer()
        self._message_timer.timeout.connect(self._read_message_queue)
        self._message_timer.start(MESSAGE_TIMER_PERIOD)

    def _cleanup(self):
        if not self._camera_capture_alive():
            return

        self._camera_scanner.kill()
        self._camera_scanner = None
        self._camera_switch = None
        self._ui.resetCountdown()

    def _cleanup_logging(self):
        self._process_logger.stop()
        self._process_logger.join()

    def initialise_scanner(self):
        self._log.debug("3) camera scanner initialisation")
        self._camera_scanner = CameraScanner(self._result_queue, self._view_queue, self._message_queue, self._config)
        self._log.debug("4) camera switch initialisation")
        self._camera_switch = CameraSwitch(self._camera_scanner, self._config.top_camera_timeout)

        self._restart_live_capture_from_side()

    def _camera_capture_alive(self):
        return self._camera_scanner is not None and self._camera_switch is not None

    def _restart_live_capture_from_top(self):
        self._log.debug("starting live capture form top")
        self._camera_switch.restart_live_capture_from_top()
        self._ui.startCountdown(self._config.top_camera_timeout.value())

    def _restart_live_capture_from_side(self):
        self._log.debug("5) starting live capture form side")
        self._reset_msg_timer()
        self._camera_switch.restart_live_capture_from_side()

    def _read_message_queue(self):
        if self._message_queue.empty():
            return

        try:
            scanner_msg = self._message_queue.get(False)
        except queue.Empty:
            return
        if isinstance(scanner_msg, CameraErrorMessage):
            self._ui.displayCameraErrorMessage(scanner_msg)
        if self._camera_switch.is_side():
            if not self._msg_timer_is_running():
                # The result queue is read at a slower rate - use a timer to give it time to process a new barcode
                self._start_msg_timer()
            elif self._has_msg_timer_timeout() and isinstance(scanner_msg, NoNewPuckBarcodeMessage):
                self._ui.displayPuckScanCompleteMessage()
                self._ui.scanCompleted()
            elif isinstance(scanner_msg, ScanErrorMessage):
                self._ui.displayScanErrorMessage(scanner_msg)
                self._reset_msg_timer()
                self._ui.resetCountdown()
        else:
            self._reset_msg_timer()

    def _reset_msg_timer(self):
        self._record_msg_timer = None

    def _start_msg_timer(self):
        self._record_msg_timer = time.time()

    def _msg_timer_is_running(self):
        return self._record_msg_timer is not None

    def _has_msg_timer_timeout(self):
        timeout = 2 * RESULT_TIMER_PERIOD / 1000
        return self._msg_timer_is_running() and time.time() - self._record_msg_timer > timeout

    def _read_view_queue(self):
        if self._view_queue.empty():
            return

        try:
            image = self._view_queue.get(False)
        except queue.Empty:
            return

        self._ui.displayPuckImage(image)

    def _read_result_queue(self):
        """ Called every second; read any new results from the scan results queue, store them and display them.
        """
        if not self._camera_capture_alive():
            return

        if self._camera_switch.is_side():
            self._read_side_scan()
        else:
            self._read_top_scan()

    def _read_side_scan(self):
        self._scan_completed_message_flag = False
        if self._result_queue.empty():
            return

        # Get the result
        plate, holder_image = self._result_queue.get(False)
        if not plate.is_full_valid():
            return

        # Barcode successfully read
        Beeper.beep()
        self._log.debug("puck barcode recorded")
        holder_barcode = plate.barcodes()[0]
        if not self._ui.isLatestHolderBarcode(holder_barcode):
            self._latest_holder_barcode = holder_barcode
            self._latest_holder_image = holder_image
            self._restart_live_capture_from_top()

    def _read_top_scan(self):
        if self._camera_switch.is_top_scan_timeout():
            extra = ({"timeout_value": 1})
            log = logging.LoggerAdapter(self._log, extra)
            log.info("scan timeout", extra)
            if self._scan_completed_message_flag:
                self._ui.displayScanCompleteMessage()
                self._ui.scanCompleted()
            else:
                self._ui.displayScanTimeoutMessage()
                self._ui.resetCountdown()
            self._restart_live_capture_from_side()
            return

        if self._result_queue.empty():
            return

        # Get the result
        plate, pins_image = self._result_queue.get(False)

        # Add new record to the table - side is the _latest_holder_barcode read first, top is the plate
        self._ui.addRecordFrame(self._latest_holder_barcode, plate, self._latest_holder_image, pins_image)

        if not plate.is_full_valid():
            self._scan_completed_message_flag = True
            return

        # Barcodes successfully read
        Beeper.beep()
        extra = ({"scan_time": self._camera_switch.get_scan_time(), "timeout_value": 0})
        log = logging.LoggerAdapter(self._log, extra)
        log.info("Scan Completed", extra)
        self._ui.displayScanCompleteMessage()
        self._ui.scanCompleted()
        self._scan_completed_message_flag = True
        self._restart_live_capture_from_side()

# should go to the cammer amanager
    def test_cameras(self):

        # Object thet has a function which tests both cammeras and returns an error message or None
        camera_top_config = self._config.get_top_camera_config()
        camera_side_config = self._config.get_side_camera_config()

        top_number = camera_top_config.camera_number.value()
        top_width = camera_top_config.width.value()
        top_height = camera_top_config.height.value()

        side_number = camera_side_config.camera_number.value()
        side_width = camera_side_config.width.value()
        side_height = camera_side_config.height.value()

        stream_top = CaptureManager(Camera(top_number, top_width, top_height))
        stream_top.create_capture()
        frame_top = stream_top.get_frame()

        stream_side = CaptureManager(Camera(side_number, side_width, side_height))
        stream_side.create_capture()
        frame_side = stream_side.get_frame()

        if frame_top is None and frame_top is None:
            return CameraErrorMessage("TOP and SIDE")
        if frame_top is None:
            return CameraErrorMessage("TOP")
        if frame_side is None:
            return CameraErrorMessage("SIDE")

        return None





