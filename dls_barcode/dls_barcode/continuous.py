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

Q_LIMIT = 4
SCANNED_TAG = "Already Scanned"


def capture_worker(camera_num, task_queue, overlay_queue, continuous_scanner):
    # Initialize camera
    cap = cv2.VideoCapture(camera_num)
    cap.set(3,1920)
    cap.set(4,1080)

    # Set snapshot interval
    img_interval = 0.5
    timer = time.time()

    lastest_overlay = Overlay(None)

    while(True):
        # Capture the next frame from the camera
        _, frame = cap.read()
        CvImage.CurrentWebcamFrame = frame

        # Add the frame to the task queue to be processed
        process_frame = time.time() - timer > img_interval
        if process_frame and task_queue.qsize() < Q_LIMIT:
            timer = time.time()
            # Make a copy of image so the overlay doesn't overwrite it
            task_queue.put(frame.copy())

        # Get the latest overlay
        while not overlay_queue.empty():
            lastest_overlay = overlay_queue.get(False)

        # Draw the overlay on the frame
        lastest_overlay.draw_on_image(frame)

        # Display the frame on the screen
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        cv2.imshow('Barcode Scanner', small)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up camera and kill the worker threads
    cap.release()
    cv2.destroyAllWindows()
    continuous_scanner.kill_workers()


def SINGLE_THREAD_scanner_worker(task_queue, overlay_queue, store):
    partial_plate = None

    while True:
        # Get next image from queue (terminate if a queue contains a 'None' sentinel)
        frame = task_queue.get(True)
        if frame is None:
            break

        # Make grayscale version of image
        cv_image = CvImage(None, frame)
        gray_image = cv_image.to_grayscale().img

        # TODO: scan but include previous plate
        plate = Scanner.ScanImage(gray_image, partial_plate)

        # Scan must be correctly aligned to be useful
        if plate.scan_ok:
            # Plate mustn't have any barcodes that match the last successful scan
            last_record = store.get_record(0)
            if last_record and last_record.any_barcode_matches(plate):
                overlay_queue.put(Overlay(None, SCANNED_TAG))
                continue

            # Attempt to merge it with the previous partial plate scan if they have any barcodes in common
            if plate.num_valid_barcodes < plate.num_slots:
                if partial_plate and plate.has_slots_in_common(partial_plate):
                    plate.merge(partial_plate)
                    partial_plate = plate
                    overlay_queue.put(Overlay(plate))
                else:
                    partial_plate = plate
                    overlay_queue.put(Overlay(plate))

            # If the plate has the required number of barcodes, store it
            if plate.num_valid_barcodes == plate.num_slots:
                overlay_queue.put(Overlay(plate))
                store_record(plate, cv_image, store)
                partial_plate = None




def perform_scan_worker(task_queue, plate_queue):
    # process image
    while True:
        # Get next image from queue, terminate if a queue contains a 'None' sentinel
        frame = task_queue.get(True)
        if frame is None:
            break

        timer = time.time()

        # Make grayscale version of image
        cv_image = CvImage(filename=None, img=frame)
        gray_image = cv_image.to_grayscale().img

        try:
            # Scan the image for barcodes
            plate = Scanner.ScanImage(gray_image)
            plate_queue.put((plate, cv_image))
        except Exception as ex:
            pass

        print("Scan Duration: {0:.3f} secs ({1} per slot)".format(time.time() - timer, (time.time() - timer)/16))


def save_record_worker(plate_queue, overlay_queue, store):
    partial_plate = None

    while True:
        # Get next result from queue (terminate if a queue contains a 'None' sentinel)
        (plate, cv_image) = plate_queue.get(True)
        if plate is None:
            break

        # Scan must be correctly aligned to be useful
        if plate.scan_ok:
            # Plate mustn't have any barcodes that match the last successful scan
            last_record = store.get_record(0)
            if last_record and last_record.any_barcode_matches(plate):
                overlay_queue.put(Overlay(None, SCANNED_TAG))
                continue

            # Attempt to merge it with the previous partial plate scan if they have any barcodes in common
            if plate.num_valid_barcodes < plate.num_slots:
                if partial_plate and plate.has_slots_in_common(partial_plate):
                    plate.merge(partial_plate)
                    partial_plate = plate
                    overlay_queue.put(Overlay(plate))
                else:
                    partial_plate = plate
                    overlay_queue.put(Overlay(plate))

            # If the plate has the required number of barcodes, store it
            if plate.num_valid_barcodes == plate.num_slots:
                overlay_queue.put(Overlay(plate))
                store_record(plate, cv_image, store)
                partial_plate = None


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
        self.result_queue = multiprocessing.Queue()
        self.num_scanners = multiprocessing.cpu_count() - 1

    def stream_webcam(self, store, camera_num):
        capture_pool = multiprocessing.Pool(1, capture_worker, (camera_num, self.task_queue, self.overlay_queue, self,))
        scanner_pool = multiprocessing.Pool(self.num_scanners, perform_scan_worker, (self.task_queue, self.result_queue,) )
        record_pool = multiprocessing.Pool(1, save_record_worker, (self.result_queue, self.overlay_queue, store,))

    def kill_workers(self):
        self.result_queue.put((None, None))
        for i in range(self.num_scanners):
            self.task_queue.put(None)


class Overlay:
    def __init__(self, plate, text=None, lifetime=1):
        self._plate = plate
        self._text = text
        self._lifetime = lifetime

        self._start_time = time.time()

    def draw_on_image(self, image):
        cv_image = CvImage(filename=None, img=image)

        if time.time() - self._start_time < self._lifetime:
            if self._plate is not None:
                self._plate.draw_plate(cv_image, CvImage.BLUE)
                self._plate.draw_pins(cv_image)

            if self._text is not None:
                cv_image.draw_text(SCANNED_TAG, cv_image.center(), CvImage.GREEN, centered=True, scale=3)
