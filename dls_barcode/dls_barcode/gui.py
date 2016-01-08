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

        self.store = Store.from_file(STORE_FILE)

        # GUI Elements
        self.tabs = None
        self.originalImageFrame = None
        self.originalImageTab = None
        self.highlightImageFrame = None
        self.highlightImageTab = None
        self.barcodeTable = None
        self.console = None

        # Variables
        self.inputFilePath = ''

        self.init_ui()

        # ---  TESTING -------
        filepath = TEST_IMAGE_PATH + "skew1.jpg"
        #self.process_image(filepath)

    def init_ui(self):
        """ Create the basic elements of the user interface
        """
        self.setGeometry(100, 100, 850, 800)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        # Create Tab control
        self.tabs = QtGui.QTabWidget()
        self.tabs.setFixedSize(700, 730)
        self.originalImageTab = QtGui.QWidget()
        self.highlightImageTab = QtGui.QWidget()
        self.tabs.addTab(self.originalImageTab, "Original")
        self.tabs.addTab(self.highlightImageTab, "Highlight")

        # Create image frames
        self.originalImageFrame = QtGui.QLabel(self.originalImageTab)
        self.originalImageFrame.setStyleSheet("background-color: black")
        self.originalImageFrame.setGeometry(0, 0, 700, 700)
        self.highlightImageFrame = QtGui.QLabel(self.highlightImageTab)
        self.highlightImageFrame.setStyleSheet("background-color: black")
        self.highlightImageFrame.setGeometry(0, 0, 700, 700)

        # Create barcode table
        self.barcodeTable = QtGui.QTableWidget()
        self.barcodeTable.setFixedWidth(110)
        self.barcodeTable.setColumnCount(1)
        self.barcodeTable.setRowCount(10)
        self.barcodeTable.setHorizontalHeaderLabels(['Barcode'])
        self.barcodeTable.setColumnWidth(0, 100)
        self.barcodeTable.clearContents()

        # Create status message console
        self.console = QtGui.QLineEdit("hello")

        # Set Window layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.tabs)
        hbox.addWidget(self.barcodeTable)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.console)
        vbox.addStretch(1)
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addLayout(vbox)
        hbox2.addStretch(1)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(hbox2)
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
        preview_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Preview', self)
        preview_action.setShortcut('Ctrl+W')
        preview_action.setStatusTip('Show webcam preview')
        preview_action.triggered.connect(ContinuousScan.stream_webcam)

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
        scan_menu.addAction(preview_action)
        scan_menu.addAction(list_action)

    def show_scanned_list_dialog(self):
        dialog = StoreDialog(self.store)
        dialog.exec_()

    def new_image_from_file(self):
        """Load a process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', TEST_IMAGE_PATH))
        if filepath:
            self.barcodeTable.clearContents()
            self.tabs.setCurrentIndex(0)
            self.originalImageFrame.clear()
            self.highlightImageFrame.clear()
            self.setWindowTitle('Diamond Puck Barcode Scanner - ' + filepath)
            self.process_image(filepath)


    def process_image(self, filepath):
        self.inputFilePath = filepath
        self.display_image_in_frame(self.inputFilePath, self.originalImageFrame)
        self.console.setText("")

        cv_image = CvImage(self.inputFilePath)
        gray_image = cv_image.to_grayscale().img
        try:
            # Scan the image for barcodes
            plate = Scanner.ScanImage(gray_image)
            self.refill_barcode_table(plate)

            # Highlight the image and display it
            self.highlight_image_plate(cv_image, plate)
            cv_image.save_as(LAST_IMAGE)
            self.display_image_in_frame(LAST_IMAGE, self.highlightImageFrame)
            self.tabs.setCurrentIndex(1)

            # If the scan was successful, store the results
            if plate.scan_ok:
                id = str(uuid.uuid4())
                filename = os.path.abspath(STORE_IMAGE_PATH + id + '.png')
                cv_image.save_as(filename)
                self.store_new_scan(plate, filename, id)

            # If an error message was generated, display it
            if plate.error:
                self.console.setText(plate.error)
        except Exception as ex:
            self.console.setText(ex.message)

    @staticmethod
    def display_image_in_frame(filename, frame):
        pixmap = QtGui.QPixmap(filename)
        frame.setPixmap(pixmap.scaled(frame.size(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        frame.setAlignment(QtCore.Qt.AlignCenter)

    def highlight_image_plate(self, cvimg, plate):
        # Draw features on image
        plate.draw_plate(cvimg, CvImage.BLUE)
        plate.draw_barcodes(cvimg, CvImage.GREEN, CvImage.RED)
        #plate.draw_pins(cvimg, CvImage.GREEN)
        plate.crop_image(cvimg)


    def store_new_scan(self, plate, imagepath, id):
        barcodes = plate.barcodes_string().split(",")
        record = Record(plate_type=plate.type, barcodes=barcodes, imagepath=imagepath, timestamp=0, id=id)
        self.store.add_record(record)

    def refill_barcode_table(self, plate):
        num_slots = plate.num_slots
        self.barcodeTable.clearContents()
        self.barcodeTable.setRowCount(num_slots)

        for index, slot in enumerate(plate.slots):
            barcode = slot.get_barcode()

            # Select appropriate background color
            if barcode == BAD_DATA_SYMBOL:
                color = StoreDialog.COLOR_RED
            elif barcode == EMPTY_SLOT_SYMBOL:
                color = StoreDialog.COLOR_GRAY
            else:
                color = StoreDialog.COLOR_GREEN

            # Set table item
            barcode = QtGui.QTableWidgetItem(barcode)
            barcode.setBackgroundColor(color)
            barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.barcodeTable.setItem(index, 0, barcode)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = BarcodeReader()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
