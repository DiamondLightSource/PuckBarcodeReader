#!/usr/bin/env python3

import sys
import os
import uuid
from PyQt4 import QtGui, QtCore

from image import CvImage
from plate import Scanner, EMPTY_SLOT_SYMBOL
from datamatrix import BAD_DATA_SYMBOL
from store import StoreDialog, Store, Record
from continuous import ContinuousScan


"""
Todo:

Currently there are two main types of error:
    1 - The datamatrix finder pattern is completely missed by the search algorithm
    2 - Matrix is read but there are too many errors. This is almost always because
        the sample locations are systematically out of alignment with the matrix
        pixels.
"""


TEST_IMAGE_PATH = '../tests/test-images/'
TEST_OUTPUT_PATH = '../../test-output/'
STORE_IMAGE_PATH = TEST_OUTPUT_PATH + 'img_store/'

STORE_FILE = TEST_OUTPUT_PATH + 'demo_store.txt'
LAST_IMAGE = TEST_OUTPUT_PATH + 'last_image.jpg'


class BarcodeReader(QtGui.QMainWindow):

    def __init__(self):
        super(BarcodeReader, self).__init__()

        # Variables
        self.inputFilePath = ''

        self.init_ui()


    def init_ui(self):
        """ Create the basic elements of the user interface
        """
        self.setGeometry(100, 100, 850, 800)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)

        self.show()

    def init_menu_bar(self):
        """Create and populate the menu bar
        """
        # load action
        load_action = QtGui.QAction(QtGui.QIcon('open.png'), '&From File...', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load image from file to scan')
        load_action.triggered.connect(self.new_image_from_file)

        # preview action
        live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self.start_live_capture)

        # exit action
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QtGui.qApp.quit)

        # scan list
        list_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Previous Scans', self)
        list_action.setShortcut('Ctrl+S')
        list_action.setStatusTip('Display list of previously scanned barcodes')
        list_action.triggered.connect(self.show_scanned_list_dialog)

        # create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menubar.addMenu('&Scan')
        scan_menu.addAction(load_action)
        scan_menu.addAction(live_action)
        scan_menu.addAction(list_action)

    def show_scanned_list_dialog(self):
        store = Store.from_file(STORE_FILE)
        dialog = StoreDialog(store)
        dialog.exec_()

    def new_image_from_file(self):
        """Load a process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', TEST_IMAGE_PATH))
        if filepath:
            self.process_image(filepath)

    def start_live_capture(self):
        store = Store.from_file(STORE_FILE)
        scanner = ContinuousScan()
        scanner.stream_webcam(store, camera_num=0)

    def process_image(self, filepath):
        self.inputFilePath = filepath

        cv_image = CvImage(self.inputFilePath)
        gray_image = cv_image.to_grayscale().img

        # Scan the image for barcodes
        plate = Scanner.ScanImage(gray_image)

        # Highlight the image and display it
        plate.draw_plate(cv_image, CvImage.BLUE)
        plate.draw_pins(cv_image)
        plate.crop_image(cv_image)
        cv_image.save_as(LAST_IMAGE)

        # If the scan was successful, store the results
        if plate.scan_ok:
            id = str(uuid.uuid4())
            filename = os.path.abspath(STORE_IMAGE_PATH + id + '.png')
            cv_image.save_as(filename)
            self.store_new_scan(plate, filename, id)

    def store_new_scan(self, plate, imagepath, id):
        barcodes = plate.barcodes()
        record = Record(plate_type=plate.type, barcodes=barcodes, imagepath=imagepath, timestamp=0, id=id)
        store = Store.from_file(STORE_FILE)
        store.add_record(record)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = BarcodeReader()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
