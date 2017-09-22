import multiprocessing
import queue

from PyQt4 import QtGui, QtCore

from dls_barcode.config import BarcodeConfig, BarcodeConfigDialog
from dls_barcode.config.barcode_config import CameraConfig
from dls_barcode.camera import CameraScanner, CameraSwitch
from dls_util import Beeper
from .barcode_table import BarcodeTable
from .image_frame import ImageFrame
from .record_table import ScanRecordTable

class DiamondBarcodeMainWindow(QtGui.QMainWindow):
    """ Main GUI window for the Barcode Scanner App.
    """
    def __init__(self, config_file):
        super(DiamondBarcodeMainWindow, self).__init__()

        self._config = BarcodeConfig(config_file)
        self._camera_config = CameraConfig(config_file)

        # UI elements
        self.recordTable = None
        self.barcodeTable = None
        self.sideBarcodeWindow = None
        self.imageFrame = None

        # Queue that holds new results generated in continuous scanning mode
        self._scan_queue = multiprocessing.Queue()
        self._view_queue = multiprocessing.Queue()
        self._initialise_scanner()

        dialog = self._init_ui()
        if not dialog.isVisible():
            # Timer that controls how often new scan results are looked for
            self._result_timer = QtCore.QTimer()
            self._result_timer.timeout.connect(self._read_scan_queue)
            self._result_timer.start(1000)

            self._result_timer1 = QtCore.QTimer()
            self._result_timer1.timeout.connect(self._read_view_queue)
            self._result_timer1.start(1)

            self._camera_switch.restart_live_capture_from_side()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        # Barcode table - lists all the barcodes in a record
        self.barcodeTable = BarcodeTable(self._config)

        # Image frame - displays image of the currently selected scan record
        self.imageFrame = ImageFrame(500, 500, "Plate Image")

        # Scan record table - lists all the records in the store
        self.recordTable = ScanRecordTable(self.barcodeTable, self.imageFrame, self._config, self)

        # Open options first to make sure the cameras are set up correctly.
        # Start live capture of the side as soon as the dialog box is closed
        dialog = self._open_options_dialog()

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.recordTable)
        hbox.addWidget(self.barcodeTable)
        vbox_new = QtGui.QVBoxLayout()
        vbox_new.addWidget(self.imageFrame)
        hbox.addLayout(vbox_new)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()
        return dialog

    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # Continuous scanner mode
        live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self._camera_switch.restart_live_capture_from_side)

        # Exit Application
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self._cleanup)
        exit_action.triggered.connect(QtGui.qApp.quit)

        # Open options dialog
        options_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Options', self)
        options_action.setShortcut('Ctrl+O')
        options_action.setStatusTip('Open Options Dialog')
        options_action.triggered.connect(self._open_options_dialog)
        options_action.triggered.connect(self._on_options_changed)  # find a better way of doing this

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Option')
        option_menu.addAction(options_action)

    def _open_options_dialog(self):
        dialog = BarcodeConfigDialog(self._config, self._camera_config) # pass the object here and trigger when the button is pressed
        dialog.exec_()
        return dialog

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._cleanup()
        event.accept()

    def _cleanup(self):
        self._camera_scanner.kill()

    def _initialise_scanner(self):
        self._camera_scanner = CameraScanner(self._scan_queue, self._view_queue, self._camera_config)
        self._camera_switch = CameraSwitch(self._camera_scanner, self._config)

    def _on_options_changed(self):
        self._cleanup()
        self._initialise_scanner()
        self._camera_switch.restart_live_capture_from_side()

    def on_record_table_clicked(self):
        self._camera_switch.stop_live_capture()

    def _read_view_queue(self):
        if not self._view_queue.empty():
            try:
                image = self._view_queue.get(False)
                self.imageFrame.display_puck_image(image)
            except queue.Empty:
                print("MAIN: Empty view queue error occured - skipping")

    def _read_scan_queue(self):
        """ Called every second; read any new results from the scan results queue, store them and display them.
        """
        if self._camera_switch.is_side():
            self._read_side_scan()
        else:
            self._read_top_scan()

    def _read_side_scan(self):
        if self._scan_queue.empty():
            return

        # Get the result
        plate, cv_image = self._scan_queue.get(False)
        if not plate.is_full_valid():
            return

        # Barcode successfully read
        Beeper.beep()
        print("MAIN: side barcode recorded")
        if self.recordTable.unique_side_barcode(plate): # if new side barcode
            self._camera_switch.restart_live_capture_from_top()
            self.original_plate = plate
            self.original_cv_image = cv_image # for merging

    def _read_top_scan(self):
        if self._scan_queue.empty():
            if self._camera_switch.is_top_scan_timeout():
                print("\n*** Scan timeout ***")
                self._camera_switch.restart_live_capture_from_side()
            return

        # Get the result
        plate, cv_image = self._scan_queue.get(False)

        # TODO:merge images
        # Store scan results and display in GUI
        # new_image = self.original_cv_image.mage_cv_ima ge(cv_image)

        # add new record to the table - side is the original_plate read first, top is the plate
        self.recordTable.add_record_frame(self.original_plate, plate, cv_image)
        if not plate.is_full_valid():
            return

        # Barcode successfully read
        Beeper.beep()
        print("Scan Recorded")
        self._camera_switch.restart_live_capture_from_side()

