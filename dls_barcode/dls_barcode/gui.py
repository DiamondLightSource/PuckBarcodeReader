#!/usr/bin/env python3

import sys
import os
import winsound
import multiprocessing
import pyperclip
from PyQt4 import QtGui, QtCore

from image import CvImage
from plate import Scanner, EMPTY_SLOT_SYMBOL
from store import Store, Record
from datamatrix import BAD_DATA_SYMBOL
from continuous import ContinuousScan

# MINOR:
# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys
# todo: Allow option to disable image saving

TEST_IMAGE_PATH = '../tests/test-images/'
TEST_OUTPUT_PATH = '../../test-output/'
STORE_IMAGE_PATH = TEST_OUTPUT_PATH + 'img_store/'
STORE_FILE = TEST_OUTPUT_PATH + 'demo_store.txt'


class BarcodeReader(QtGui.QMainWindow):

    COLUMNS = ['Date', 'Time', 'Plate Type', 'Valid', 'Invalid', 'Empty']
    COLOR_RED = QtGui.QColor(255, 0, 0, 128)
    COLOR_GREEN = QtGui.QColor(0, 255, 0, 128)
    COLOR_ORANGE = QtGui.QColor(255,128,0, 128)

    def __init__(self):
        super(BarcodeReader, self).__init__()

        self._store = Store.from_file(STORE_FILE)

        # Queue that holds new results generated in continuous scanning mode
        self._new_scan_queue = multiprocessing.Queue()

        # Timer that controls how often new scan results are looked for
        self._result_timer = QtCore.QTimer()
        self._result_timer.timeout.connect(self._read_new_scan_queue)
        self._result_timer.start(1000)

        # UI elements
        self._recordTable = None
        self._barcodeTable = None
        self._imageFrame = None

        self._init_ui()
        self._load_store_records(self._store)

    def _read_new_scan_queue(self):
        """ Called every second; read any new results from the scan results queue,
        store them and display them.
        """
        if not self._new_scan_queue.empty():
            # Get the result
            plate, cv_image = self._new_scan_queue.get(False)

            # Notify user of new scan
            print "Scan Recorded"
            winsound.Beep(4000, 500) # frequency, duration

            # Store scan results and display in GUI
            self._store.add_record(plate.type, plate.barcodes(), cv_image)
            self._load_store_records(self._store)

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        # Create record table - lists all the records in the store
        self._recordTable = QtGui.QTableWidget(self)
        self._recordTable.setFixedWidth(420)
        self._recordTable.setFixedHeight(600)
        self._recordTable.setColumnCount(len(self.COLUMNS))
        self._recordTable.setHorizontalHeaderLabels(self.COLUMNS)
        self._recordTable.setColumnWidth(0, 70)
        self._recordTable.setColumnWidth(1, 55)
        self._recordTable.setColumnWidth(2, 85)
        self._recordTable.setColumnWidth(3, 60)
        self._recordTable.setColumnWidth(4, 60)
        self._recordTable.setColumnWidth(5, 60)
        self._recordTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._recordTable.cellPressed.connect(self._record_selected)

        # Create barcode table - lists all the barcode sin a record
        self._barcodeTable = QtGui.QTableWidget()
        self._barcodeTable.setFixedWidth(110)
        self._barcodeTable.setFixedHeight(600)
        self._barcodeTable.setColumnCount(1)
        self._barcodeTable.setRowCount(10)
        self._barcodeTable.setHorizontalHeaderLabels(['Barcode'])
        self._barcodeTable.setColumnWidth(0, 100)

        # Image frame - displays image of the currently selected scan record
        self._imageFrame = QtGui.QLabel()
        self._imageFrame.setStyleSheet("background-color: black; color: red; font-size: 30pt; text-align: center")
        self._imageFrame.setFixedWidth(600)
        self._imageFrame.setFixedHeight(600)

        # Delete button - deletes selected records
        deleteBtn = QtGui.QPushButton('Delete')
        deleteBtn.setToolTip('Delete selected scan/s')
        deleteBtn.resize(deleteBtn.sizeHint())
        deleteBtn.clicked.connect(self._delete_selected_records)

        # Clipboard button - copy the selected barcodes to the clipboard
        clipboardBtn = QtGui.QPushButton('Copy To Clipboard')
        clipboardBtn.setToolTip('Copy barcodes for the selected record to the clipboard')
        clipboardBtn.resize(clipboardBtn.sizeHint())
        clipboardBtn.clicked.connect(self._copy_selected_records_to_clipboard)

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self._recordTable)
        hbox.addWidget(self._barcodeTable)
        hbox.addWidget(self._imageFrame)
        hbox.addStretch(1)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.setSpacing(10)
        hbox2.addWidget(clipboardBtn)
        hbox2.addWidget(deleteBtn)
        hbox2.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addStretch(1)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()

    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # load action
        load_action = QtGui.QAction(QtGui.QIcon('open.png'), '&From File...', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load image from file to scan')
        load_action.triggered.connect(self._scan_file_image)

        # preview action
        live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self._start_live_capture)

        # exit action
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QtGui.qApp.quit)

        # create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(load_action)
        scan_menu.addAction(live_action)

    def _scan_file_image(self):
        """Load and process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', TEST_IMAGE_PATH))
        if filepath:
            cv_image = CvImage(filepath)
            gray_image = cv_image.to_grayscale().img

            # Scan the image for barcodes
            plate = Scanner.ScanImage(gray_image)

            # Highlight the image and display it
            plate.draw_plate(cv_image, CvImage.BLUE)
            plate.draw_pins(cv_image)
            plate.crop_image(cv_image)

            # If the scan was successful, store the results
            if plate.scan_ok:
                self._store.add_record(plate.type, plate.barcodes(), cv_image)
                self._load_store_records(self._store)

    def _start_live_capture(self):
        """ Starts the process of continuous capture from an attached camera.
        """
        scanner = ContinuousScan(self._new_scan_queue)
        scanner.stream_webcam(camera_num=0)

    def _load_store_records(self, store):
        """ Populate the record table with all of the records in the store.
        """
        self._recordTable.clearContents()
        self._recordTable.setRowCount(self._store.size())

        for n, record in enumerate(store.records):
            items = [record.date, record.time, record.plate_type, record.num_valid_barcodes,
                     record.num_invalid_barcodes, record.num_empty_slots]

            if record.num_valid_barcodes == record.num_slots:
                color = self.COLOR_GREEN
            else:
                color = self.COLOR_RED


            for m, item in enumerate(items):
                newitem = QtGui.QTableWidgetItem(str(item))
                newitem.setBackgroundColor(color)
                newitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self._recordTable.setItem(n, m, newitem)

        self._barcodeTable.clearContents()
        self._display_record_image(None)

    def _record_selected(self):
        """ Called when a row is selected, causes details of the selected record to be
        displayed (list of barcodes in the barcode table and image of the scan in the
        image frame).
        """
        try:
            row = self._recordTable.selectionModel().selectedRows()[0].row()
            record = self._store.get_record(row)
            self._fill_barcode_table(record.barcodes)
            self._display_record_image(record.imagepath)
        except IndexError:
            self._fill_barcode_table([])
            self._display_record_image(None)

    def _fill_barcode_table(self, barcodes):
        """ Called when a new row is selected on the record table. Displays all of the
        barcodes from the selected record in the barcode table. Valid barcodes are
        highlighted green, invalid barcodes are highlighted red, and empty slots are grey.
        """
        num_slots = len(barcodes)
        self._barcodeTable.clearContents()
        self._barcodeTable.setRowCount(num_slots)

        for index, barcode in enumerate(barcodes):
            # Select appropriate background color
            if barcode == BAD_DATA_SYMBOL:
                color = self.COLOR_ORANGE
            elif barcode == EMPTY_SLOT_SYMBOL:
                color = self.COLOR_RED
            else:
                color = self.COLOR_GREEN

            # Set table item
            barcode = QtGui.QTableWidgetItem(barcode)
            barcode.setBackgroundColor(color)
            barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self._barcodeTable.setItem(index, 0, barcode)

    def _display_record_image(self, filename):
        """ Called when a new row is selected on the record table. Displays the specified
        image (image of the highlighted scan) in the image frame
        """
        self._imageFrame.clear()
        self._imageFrame.setAlignment(QtCore.Qt.AlignCenter)

        if filename is None:
            self._imageFrame.setText("No Scan Selected")
        elif os.path.isfile(filename):
            pixmap = QtGui.QPixmap(filename)
            self._imageFrame.setPixmap(pixmap.scaled(self._imageFrame.size(),
                                                     QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self._imageFrame.setText("Image Not Found")


    def _delete_selected_records(self):
        """ Called when the 'Delete' button is pressed. Deletes all of the selected records
        (and the associated images) from the store and from disk. Asks for user confirmation.
        """
        # Display a confirmation dialog to check that user wants to proceed with deletion
        quit_msg = "This operation cannot be undone.\nAre you sure you want to delete these record/s?"
        reply = QtGui.QMessageBox.warning(self, 'Confirm Delete',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        # If yes, find the appropriate records and delete them
        if reply == QtGui.QMessageBox.Yes:
            rows = self._recordTable.selectionModel().selectedRows()
            records_to_delete = []
            for row in rows:
                index = row.row()
                record = self._store.get_record(index)
                records_to_delete.append(record)

            self._store.delete_records(records_to_delete)
            self._load_store_records(self._store)

    def _copy_selected_records_to_clipboard(self):
        """ Called when the copy to clipboard button is pressed. Copies the list/s of
        barcodes for the currently selected records to the clipboard so that the user
        can paste it elsewhere.
        """
        rows = self._recordTable.selectionModel().selectedRows()
        rows = sorted([row.row() for row in rows])
        barcodes = []
        for row in rows:
            record = self._store.get_record(row)
            barcodes.extend(record.barcodes)

        if barcodes:
            pyperclip.copy('\n'.join(barcodes))
        #spam = pyperclip.paste()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = BarcodeReader()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
