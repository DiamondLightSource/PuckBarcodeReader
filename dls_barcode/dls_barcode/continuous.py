from pkg_resources import require;  require('numpy')
import cv2

import os
import uuid
import time
import winsound
import multiprocessing
from PyQt4 import QtGui, QtCore

from store import Record


from image import CvImage

def capture_worker(camera_num, task_queue, continuous_scanner):

    # Initialize camera
    cap = cv2.VideoCapture(camera_num)
    cap.set(3,1920)
    cap.set(4,1080)

    # Set snapshot interval
    img_interval = 0.33
    timer = time.time()

    while(True):
        _, frame = cap.read()
        CvImage.CurrentWebcamFrame = frame
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        cv2.imshow('Barcode Scanner', small)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if time.time() - timer > img_interval:
            timer = time.time()
            task_queue.put(frame)

    cap.release()
    cv2.destroyAllWindows()
    print("Capture terminating...")
    continuous_scanner.kill_workers()

def perform_scan_worker(task_queue, plate_queue):
    # process image
    from plate import Scanner

    while True:
        # Get next image from queue, terminate if a queue contains a 'None' sentinel
        frame = task_queue.get(True)
        if frame is None:
            break

        timer = time.time()
        cv_image = CvImage(filename=None, img=frame)
        gray_image = cv_image.to_grayscale().img

        try:
            # Scan the image for barcodes
            plate = Scanner.ScanImage(gray_image)
            plate_queue.put((plate, cv_image))
        except Exception as ex:
            pass

        print("Scan Duration: {0:.3f} secs".format(time.time() - timer))

    print("Scanner terminating...")

def save_record_worker(plate_queue, store):
    # TODO: store list of recent scans that haven't met the required number; try to combine them together to make a whole scan

    # TODO: this is hardcoded at present
    REQUIRED_BARCODES = 10

    while True:
        # Get next result from queue, terminate if a queue contains a 'None' sentinel
        (plate, cv_image) = plate_queue.get(True)
        if plate is None:
            break

        # Scan must be correctly aligned to be useful
        if plate.scan_ok:
            # Image must have a full puck
            print("{} Barcodes in scan".format(plate.num_valid_barcodes))

            if plate.num_valid_barcodes == REQUIRED_BARCODES:
                # Plate mustn't have any barcodes that match the last successful scan
                last_record = store.get_record(0)

                if not last_record or not last_record.any_barcode_matches(plate):
                    store_record(plate, cv_image, store)

    print("Result Processor terminating...")



def store_record(plate, cv_image, store):

    # Save the scan results to the store
    print "Scan Recorded"
    winsound.Beep(4000, 500) # frequency, duration

    plate.draw_plate(cv_image, CvImage.BLUE)
    plate.draw_barcodes(cv_image, CvImage.GREEN, CvImage.RED)
    plate.crop_image(cv_image)

    id = str(uuid.uuid4())
    STORE_IMAGE_PATH = '../../test-output/img_store/'
    filename = os.path.abspath(STORE_IMAGE_PATH + id + '.png')
    cv_image.save_as(filename)
    barcodes = plate.barcodes()
    record = Record(plate_type=plate.type, barcodes=barcodes, imagepath=filename, timestamp=0, id=id)
    store.add_record(record)



class ContinuousScan():

    def __init__(self):
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.num_scanners = multiprocessing.cpu_count()



    def stream_webcam(self, store, camera_num):
        capture_pool = multiprocessing.Pool(1, capture_worker, (camera_num, self.task_queue, self) )
        scanner_pool = multiprocessing.Pool(self.num_scanners, perform_scan_worker, (self.task_queue, self.result_queue,) )
        record_pool = multiprocessing.Pool(1, save_record_worker, (self.result_queue, store,))

    def kill_workers(self):
        self.result_queue.put((None, None))
        for i in range(self.num_scanners):
            self.task_queue.put(None)




