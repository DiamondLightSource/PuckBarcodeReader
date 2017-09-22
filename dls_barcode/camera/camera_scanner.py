from __future__ import division

import multiprocessing
import time

from dls_util.image import Image, Color
from dls_util import Beeper
from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_barcode.datamatrix import DataMatrix
from .overlay import PlateOverlay, TextOverlay
from .capture_worker import CaptureWorker
from .camera_position import CameraPosition
from .stream_action import StreamAction
from .capture_command import CaptureCommand

Q_LIMIT = 1
SCANNED_TAG = "Scan Complete"
NO_PUCK_TIME = 2

EXIT_KEY = 'q'

# Maximum frame rate to sample at (rate will be further limited by speed at which frames can be processed)
MAX_SAMPLE_RATE = 10.0
INTERVAL = 1.0 / MAX_SAMPLE_RATE


class CameraScanner:
    """ Manages the continuous scanning mode which takes a live feed from an attached camera and
    periodically scans the images for plates and barcodes. Multiple partial images are combined
    together until enough barcodes are scanned to make a full plate.

    Two separate processes are spawned, one to handle capturing and displaying images from the cameras,
    and the other to handle processing (scanning) of those images.
    """
    def __init__(self, result_queue, view_queue, camera_config):
        """ The task queue is used to store a queue of captured frames to be processed; the overlay
        queue stores Overlay objects which are drawn on to the image displayed to the user to highlight
        certain features; and the result queue is used to pass on the results of successful scans to
        the object that created the scanner.
        """
        self._task_q = multiprocessing.Queue()
        self._overlay_q = multiprocessing.Queue()
        self._capture_command_q = multiprocessing.Queue()
        self._capture_kill_q = multiprocessing.Queue()
        self._scanner_kill_q = multiprocessing.Queue()
        self._result_q = result_queue
        self._view_q = view_queue

        self._camera_configs = {CameraPosition.SIDE: camera_config.getSideCameraConfig(),
                          CameraPosition.TOP: camera_config.getPuckCameraConfig()}

        capture_args = (self._task_q, self._view_q, self._overlay_q, self._capture_command_q, self._capture_kill_q,
                        self._camera_configs)

        # The capture process is always running: we initialise the cameras only once because it's time consuming
        self._capture_process = multiprocessing.Process(target=_capture_worker, args=capture_args)
        self._capture_process.start()

        self._scanner_process = None

    def start_scan(self, cam_position, config):
        """ Spawn the processes that will continuously capture and process images from the camera.
        """
        print("\nMAIN: start triggered")
        scanner_args = (self._task_q, self._overlay_q, self._result_q, self._scanner_kill_q, config,
                        self._camera_configs[cam_position])
        self._scanner_process = multiprocessing.Process(target=_scanner_worker, args=scanner_args)

        self._capture_command_q.put(CaptureCommand(StreamAction.START, cam_position))
        self._scanner_process.start()

    def stop_scan(self):
        print("\nMAIN: Stop triggered")
        self._capture_command_q.put(CaptureCommand(StreamAction.STOP))
        if self._scanner_process is not None:
            self._scanner_kill_q.put(None)
            self._scanner_process.join()
            self._flush_queue(self._scanner_kill_q)
            self._scanner_process = None
            print("MAIN: scanner rejoined")

        print("MAIN: Stop completed")

    def kill(self):
        print("\n__________")
        print("MAIN: Kill")
        self.stop_scan()
        self._capture_kill_q.put(None)
        self._capture_process.join()
        print("MAIN: KILL COMPLETED")

    def _flush_queue(self, queue):
        while not queue.empty():
            queue.get()


def _capture_worker(task_queue, view_queue, overlay_queue, command_queue, kill_queue, camera_configs):
    """ Function used as the main loop of a worker process.
    """
    worker = CaptureWorker(camera_configs)
    worker.run(task_queue, view_queue, overlay_queue, command_queue, kill_queue)


def _scanner_worker(task_queue, overlay_queue, result_queue, kill_queue, config, camera_config):
    """ Function used as the main loop of a worker process. Scan images for barcodes,
    combining partial scans until a full puck is reached.

    Keep the record of the last scan which was at least partially successful (aligned geometry
    and some barcodes scanned). For each new frame, we can attempt to merge the results with
    this previous plates so that we don't have to re-read any of the previously captured barcodes
    (because this is a relatively expensive operation).
    """
    print("SCANNER start")
    last_plate_time = time.time()

    SlotScanner.DEBUG = config.slot_images.value()
    SlotScanner.DEBUG_DIR = config.slot_image_directory.value()

    if ("Side" in camera_config[0]._tag):
        # Side camera
        plate_type = "None"
        barcode_sizes = DataMatrix.DEFAULT_SIDE_SIZES
    else:
        # Top camera
        plate_type = config.plate_type.value()
        barcode_sizes = [config.top_barcode_size.value()]

    if plate_type == "None":
        scanner = OpenScanner(barcode_sizes)
    else:
        scanner = GeometryScanner(plate_type, barcode_sizes)

    display = True
    while kill_queue.empty():
        if display:
            print("--- scanner inside loop")
            display = False
        if task_queue.empty():
            continue

        frame = task_queue.get(True)

        # Make grayscale version of image
        image = Image(frame)
        gray_image = image.to_grayscale()

        # If we have an existing partial plate, merge the new plate with it and only try to read the
        # barcodes which haven't already been read. This significantly increases efficiency because
        # barcode read is expensive.
        scan_result = scanner.scan_next_frame(gray_image)

        if config.console_frame.value():
            scan_result.print_summary()

        if scan_result.success():
            # Record the time so we can see how long its been since we last saw a plate
            last_plate_time = time.time()

            plate = scan_result.plate()

            if scan_result.already_scanned():
                overlay_queue.put(TextOverlay(SCANNED_TAG, Color.Green()))
            elif scan_result.any_valid_barcodes():
                overlay_queue.put(PlateOverlay(plate, config))
                _plate_beep(plate, config)

            if scan_result.any_new_barcodes():
                result_queue.put((plate, image))
        else:
            time_since_plate = time.time() - last_plate_time
            if time_since_plate > NO_PUCK_TIME:
                overlay_queue.put(TextOverlay(scan_result.error(), Color.Red()))

    # Flush the queues for which this process is a writer
    while not result_queue.empty():
        result_queue.get()
    print("--- scanner result Q flushed")

    while not overlay_queue.empty():
        overlay_queue.get()
    print("--- scanner overlay Q flushed")
    print("SCANNER stop & kill")


def _plate_beep(plate, options):
    if not options.scan_beep.value():
        return

    empty_fraction = (plate.num_slots - plate.num_valid_barcodes()) / plate.num_slots
    frequency = int(10000 * empty_fraction + 37)
    duration = 200
    Beeper.beep(frequency, duration)
