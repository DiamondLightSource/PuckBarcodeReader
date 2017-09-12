from __future__ import division

import multiprocessing
import time
try:
    import winsound
except ImportError:
    import os
    def playsound(frequency,duration):
        #apt-get install beep
        os.system('beep -f %s -l %s' % (frequency,duration))
else:
    def playsound(frequency,duration):
        winsound.Beep(frequency,duration)

import cv2

from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_util.image import Image, Color
from dls_barcode.datamatrix.read import DatamatrixSizeTable
from .overlay import PlateOverlay, TextOverlay, Overlay

_OPENCV_MAJOR = cv2.__version__[0]

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

    Two separate processes are spawned, one to handle capturing and displaying images from the camera,
    and the other to handle processing (scanning) of those images.
    """
    def __init__(self, result_queue, view_queue):
        """ The task queue is used to store a queue of captured frames to be processed; the overlay
        queue stores Overlay objects which are drawn on to the image displayed to the user to highlight
        certain features; and the result queue is used to pass on the results of successful scans to
        the object that created the ContinuousScan.
        """
        self.task_queue = multiprocessing.Queue()
        self.overlay_queue = multiprocessing.Queue()
        self.kill_queue = multiprocessing.Queue()
        self.result_queue = result_queue
        self.view_queue = view_queue

    def stream_camera(self, config, camera_config):
        """ Spawn the processes that will continuously capture and process images from the camera.
        """
        capture_args = (self.task_queue, self.overlay_queue, self.kill_queue, self.view_queue, camera_config)
        scanner_args = (self.task_queue, self.overlay_queue, self.result_queue, self.kill_queue, config, camera_config)

        capture_process = multiprocessing.Process(target=_capture_worker, args=capture_args)
        scanner_process = multiprocessing.Process(target=_scanner_worker, args=scanner_args)

        capture_process.start()
        scanner_process.start()

    def kill(self):
        self.kill_queue.put(None)


def _capture_worker(task_queue, overlay_queue, kill_queue, view_queue, camera_config):
    """ Function used as the main loop of a worker process. Continuously captures images from
    the camera and puts them on a queue to be processed. The images are displayed (as video)
    to the user with appropriate highlights (taken from the overlay queue) which indicate the
    position of scanned and unscanned barcodes.
    """
    # Initialize the camera
    cap = cv2.VideoCapture(camera_config[0].value())
    read_ok, _ = cap.read()
    if not read_ok:
        cap = cv2.VideoCapture(0)

    if _OPENCV_MAJOR == '2':
        width_flag = cv2.cv.CV_CAP_PROP_FRAME_COUNT
        height_flag = cv2.cv.CV_CAP_PROP_FRAME_COUNT
    else:
        width_flag = cv2.CAP_PROP_FRAME_WIDTH
        height_flag = cv2.CAP_PROP_FRAME_HEIGHT

    cap.set(width_flag, camera_config[1].value())
    cap.set(height_flag, camera_config[2].value())

    # Store the latest image overlay which highlights the puck
    latest_overlay = Overlay(0)
    last_time = time.time()

    while kill_queue.empty():
        # Capture the next frame from the camera
        read_ok, frame = cap.read()

        # Add the frame to the task queue to be processed
        # NOTE: the rate at which frames are pushed to the task queue is lower than the rate at which frames are acquired
        if task_queue.qsize() < Q_LIMIT and (time.time() - last_time >= INTERVAL):
            # Make a copy of image so the overlay doesn't overwrite it
            task_queue.put(frame.copy())
            last_time = time.time()

        # All frames (scanned or not) are pushed to the view queue for display
        # Get the latest overlay - it won't be generated from the current frame but it doesn't matter
        while not overlay_queue.empty():
            latest_overlay = overlay_queue.get(False)

        # Draw the overlay on the frame
        latest_overlay.draw_on_image(frame)

        view_queue.put(Image(frame))

    # Clean up camera
    cap.release()
    cv2.destroyAllWindows()

    # Flush the queues for which this process is a writer
    while not task_queue.empty():
        task_queue.get()

    while not view_queue.empty():
        view_queue.get()


def _scanner_worker(task_queue, overlay_queue, result_queue, kill_queue, options, camera_config):
    """ Function used as the main loop of a worker process. Scan images for barcodes,
    combining partial scans until a full puck is reached.

    Keep the record of the last scan which was at least partially successful (aligned geometry
    and some barcodes scanned). For each new frame, we can attempt to merge the results with
    this previous plates so that we don't have to re-read any of the previously captured barcodes
    (because this is a relatively expensive operation).
    """
    last_plate_time = time.time()

    SlotScanner.DEBUG = options.slot_images.value()
    SlotScanner.DEBUG_DIR = options.slot_image_directory.value()

    if ("Side" in camera_config[0]._tag):
        # Side camera
        plate_type = "None"
        barcode_sizes = DatamatrixSizeTable.valid_sizes()
    else:
        # Top camera
        plate_type = options.plate_type.value()
        barcode_sizes = [options.top_barcode_size.value()]

    if plate_type == "None":
        scanner = OpenScanner(barcode_sizes)
    else:
        scanner = GeometryScanner(plate_type, barcode_sizes)

    while kill_queue.empty():
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

        if options.console_frame.value():
            scan_result.print_summary()

        if scan_result.success():
            # Record the time so we can see how long its been since we last saw a plate
            last_plate_time = time.time()

            plate = scan_result.plate()

            if scan_result.already_scanned():
                overlay_queue.put(TextOverlay(SCANNED_TAG, Color.Green()))
            elif scan_result.any_valid_barcodes():
                overlay_queue.put(PlateOverlay(plate, options))
                _plate_beep(plate, options)

            if scan_result.any_new_barcodes():
                result_queue.put((plate, image))
        else:
            time_since_plate = time.time() - last_plate_time
            if time_since_plate > NO_PUCK_TIME:
                overlay_queue.put(TextOverlay(scan_result.error(), Color.Red()))

    # Flush the queues for which this process is a writer
    while not result_queue.empty():
        result_queue.get()

    while not overlay_queue.empty():
        overlay_queue.get()


def _plate_beep(plate, options):
    if not options.scan_beep.value():
        return

    empty_fraction = (plate.num_slots - plate.num_valid_barcodes()) / plate.num_slots
    frequency = int(10000 * empty_fraction + 37)
    duration = 200
    winsound.Beep(frequency, duration)
