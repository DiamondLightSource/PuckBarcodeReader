from pkg_resources import require;  require('numpy')
import cv2

import os
import uuid
import time
import winsound
import multiprocessing

from store import Record
from image import CvImage
from plate import Scanner

# TODO: Handle non-full pucks

Q_LIMIT = 1
SCANNED_TAG = "Already Scanned"

MAX_SAMPLE_RATE = 10.0
INTERVAL = 1.0 / MAX_SAMPLE_RATE


def capture_worker(camera_num, task_queue, overlay_queue):
    # Initialize camera
    cap = cv2.VideoCapture(camera_num)
    cap.set(3,1920)
    cap.set(4,1080)

    # Store the latest image overlay which highlights the puck
    lastest_overlay = Overlay(None)
    last_time = time.time()

    while(True):
        # Capture the next frame from the camera
        _, frame = cap.read()
        CvImage.CurrentWebcamFrame = frame

        # Add the frame to the task queue to be processed
        if task_queue.qsize() < Q_LIMIT and (time.time() - last_time >= INTERVAL):
            # Make a copy of image so the overlay doesn't overwrite it
            task_queue.put(frame.copy())
            last_time = time.time()

        # Get the latest overlay
        while not overlay_queue.empty():
            lastest_overlay = overlay_queue.get(False)

        # Draw the overlay on the frame
        lastest_overlay.draw_on_image(frame)

        # Display the frame on the screen
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        cv2.imshow('Barcode Scanner', small)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            task_queue.put(None)
            break

    # Clean up camera and kill the worker threads
    cap.release()
    cv2.destroyAllWindows()


def scanner_worker(task_queue, overlay_queue, store):
    # Keep the record of the last scan which was at least partially successful (aligned geometry
    # and some barcodes scanned). For each new frame, we can attempt to merge the results with
    # this previous plates so that we don't have to re-read any of the previously captured barcodes
    # (because this is a relatively expensive operation).
    last_plate = None
    frame_contains_barcodes = False

    while True:
        # Get next image from queue (terminate if a queue contains a 'None' sentinel)
        frame = task_queue.get(True)
        if frame is None:
            break

        timer = time.time()

        # Make grayscale version of image
        cv_image = CvImage(None, frame)
        gray_image = cv_image.to_grayscale().img

        # If we have an existing partial plate, merge the new plate with it and only try to read the
        # barcodes which haven't already been read. This significantly increases efficiency because
        # barcode read is expensive.
        if last_plate is None:
            plate = Scanner.ScanImage(gray_image)
        else:
            plate, frame_contains_barcodes = Scanner.ScanImageContinuous(gray_image, last_plate)

        # Scan must be correctly aligned to be useful
        if plate.scan_ok:
            # Plate mustn't have any barcodes that match the last successful scan
            last_plate = plate
            last_record = store.get_record(0)
            if last_record and last_record.any_barcode_matches(plate):
                if frame_contains_barcodes:
                    overlay_queue.put(Overlay(None, SCANNED_TAG))
            else:
                # If the plate has the required number of barcodes, store it
                if plate.is_full_valid():
                    store_record(plate, cv_image, store)

                if frame_contains_barcodes:
                    overlay_queue.put(Overlay(plate))

        print("Scan Duration: {0:.3f} secs".format(time.time() - timer))


def store_record(plate, cv_image, store):

    # Save the scan results to the store
    print "Scan Recorded"
    winsound.Beep(4000, 500) # frequency, duration

    Overlay(plate).draw_on_image(cv_image.img)
    plate.crop_image(cv_image)

    id = str(uuid.uuid4())
    STORE_IMAGE_PATH = '../../test-output/img_store/'
    filename = os.path.abspath(STORE_IMAGE_PATH + id + '.png')
    cv_image.save_as(filename)
    barcodes = plate.barcodes()
    record = Record(plate_type=plate.type, barcodes=barcodes, imagepath=filename, timestamp=0, id=id)
    store.add_record(record)


class ContinuousScan:

    def __init__(self):
        self.task_queue = multiprocessing.Queue()
        self.overlay_queue = multiprocessing.Queue()

    def stream_webcam(self, store, camera_num):
        capture_pool = multiprocessing.Pool(1, capture_worker, (camera_num, self.task_queue, self.overlay_queue,))
        scanner_pool = multiprocessing.Pool(1, scanner_worker, (self.task_queue, self.overlay_queue, store,))

    def kill_workers(self):
        self.task_queue.put(None)
        self.task_queue.put(None)


class Overlay:
    def __init__(self, plate, text=None, lifetime=1):
        self._plate = plate
        self._text = text
        self._lifetime = lifetime

        self._start_time = time.time()

    def draw_on_image(self, image):
        cv_image = CvImage(filename=None, img=image)

        if (time.time() - self._start_time) < self._lifetime:
            if self._plate is not None:
                self._plate.draw_plate(cv_image, CvImage.BLUE)
                self._plate.draw_pins(cv_image)

            if self._text is not None:
                cv_image.draw_text(SCANNED_TAG, cv_image.center(), CvImage.GREEN, centered=True, scale=4, thickness=3)
