import multiprocessing
import os
import sys
import winsound

import pyperclip
from PyQt4 import QtGui, QtCore

sys.path.append("..")

from dls_barcode.plate import Scanner
from dls_barcode.util import Image
from dls_barcode.gui.options_dialog import OptionsDialog
from dls_barcode.camera_scanner import CameraScanner
from dls_barcode.program_options import ProgramOptions

from dls_barcode.gui import ScanRecordTable, BarcodeTable, ImageFrame

TEST_IMAGE_PATH = '../tests/test-resources/'
TEST_OUTPUT_PATH = '../test-output/'


class DiamondBarcodeReader(QtGui.QMainWindow):
    CONFIG_FILE = "../config.ini"

    def __init__(self):
        super(DiamondBarcodeReader, self).__init__()

        # Create directories if missing
        if not os.path.exists(TEST_OUTPUT_PATH):
            os.makedirs(TEST_OUTPUT_PATH)

        self._options = ProgramOptions(DiamondBarcodeReader.CONFIG_FILE)

        # Queue that holds new results generated in continuous scanning mode
        self._new_scan_queue = multiprocessing.Queue()

        # Timer that controls how often new scan results are looked for
        self._result_timer = QtCore.QTimer()
        self._result_timer.timeout.connect(self._read_new_scan_queue)
        self._result_timer.start(1000)

        # UI elements
        self.recordTable = None
        self.barcodeTable = None
        self.imageFrame = None

        self._init_ui()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        # Barcode table - lists all the barcodes in a record
        self.barcodeTable = BarcodeTable()

        # Image frame - displays image of the currently selected scan record
        self.imageFrame = ImageFrame()

        # Scan record table - lists all the records in the store
        # TODO - do linking with events
        self.recordTable = ScanRecordTable(self.barcodeTable, self.imageFrame, self._options)

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.recordTable)
        hbox.addWidget(self.barcodeTable)
        hbox.addWidget(self.imageFrame)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()

    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # Load from file action
        load_action = QtGui.QAction(QtGui.QIcon('open.png'), '&From File...', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load image from file to scan')
        load_action.triggered.connect(self._scan_file_image)

        # Continuous scanner mode
        live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self._start_live_capture)

        # Exit Application
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QtGui.qApp.quit)

        # Open options dialog
        options_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Options', self)
        options_action.setShortcut('Ctrl+O')
        options_action.setStatusTip('Open Options Dialog')
        options_action.triggered.connect(self._open_options_dialog)

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(load_action)
        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Option')
        option_menu.addAction(options_action)

    def _open_options_dialog(self):
        dialog = OptionsDialog(self._options)
        dialog.exec_()

    def _read_new_scan_queue(self):
        """ Called every second; read any new results from the scan results queue,
        store them and display them.
        """
        if not self._new_scan_queue.empty():
            # Get the result
            plate, cv_image = self._new_scan_queue.get(False)

            # Store scan results and display in GUI
            self.recordTable.add_record_frame(plate.type, plate.barcodes(), cv_image)

            if plate.is_full_valid():
                # Notify user of new scan
                print("Scan Recorded")
                winsound.Beep(4000, 500)  # frequency, duration

    def _scan_file_image(self):
        """Load and process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', TEST_IMAGE_PATH))
        if filepath:
            cv_image = Image(filepath)
            gray_image = cv_image.to_grayscale()

            # Scan the image for barcodes
            plate, _ = Scanner(self._options).scan_next_frame(gray_image, single_image=True)

            # If the scan was successful, store the results
            if plate is not None:
                # Highlight the image and display it
                plate.draw_plate(cv_image, Image.BLUE)
                plate.draw_pins(cv_image)
                plate.crop_image(cv_image)

                self.recordTable.add_record(plate.type, plate.barcodes(), cv_image)
            else:
                QtGui.QMessageBox.warning(self, "Scanning Error",
                                          "There was a problem scanning the image.\n" + plate.error)

    def _start_live_capture(self):
        """ Starts the process of continuous capture from an attached camera.
        """
        scanner = CameraScanner(self._new_scan_queue)
        scanner.stream_camera(camera_num=0, options=self._options)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = DiamondBarcodeReader()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
