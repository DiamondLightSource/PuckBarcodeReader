import multiprocessing
import queue

from PyQt4 import QtGui, QtCore

from dls_barcode.config import BarcodeConfig, BarcodeConfigDialog
from dls_barcode.camera import CameraScanner, CameraSwitch
from dls_util import Beeper
from dls_util.file import FileManager
from .barcode_table import BarcodeTable
from .image_frame import ImageFrame
from .record_table import ScanRecordTable


class DiamondBarcodeMainWindow(QtGui.QMainWindow):
    """ Main GUI window for the Barcode Scanner App.
    """
    def __init__(self, config_file):
        super(DiamondBarcodeMainWindow, self).__init__()

        self._config = BarcodeConfig(config_file, FileManager())

        # UI elements
        self.recordTable = None
        self.barcodeTable = None
        self.sideBarcodeWindow = None
        self.imageFrame = None

        # Scan elements
        self._camera_scanner = None
        self._camera_switch = None

        self._init_ui()

        # Queue that holds new results generated in continuous scanning mode
        self._result_queue = multiprocessing.Queue()
        self._view_queue = multiprocessing.Queue()
        self._message_queue = multiprocessing.Queue()
        self._initialise_scanner()

        # Timer that controls how often new scan results are looked for
        self._result_timer = QtCore.QTimer()
        self._result_timer.timeout.connect(self._read_result_queue)
        self._result_timer.start(1000)

        self._view_timer = QtCore.QTimer()
        self._view_timer.timeout.connect(self._read_view_queue)
        self._view_timer.start(1)

        self._message_timer = QtCore.QTimer()
        self._message_timer.timeout.connect(self._read_message_queue)
        self._message_timer.start(1)

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
        self.recordTable = ScanRecordTable(self.barcodeTable, self.imageFrame, self._config, self.on_record_table_clicked)

        # Open options first to make sure the cameras are set up correctly.
        # Start live capture of the side as soon as the dialog box is closed
        self._open_options_dialog()

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

    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # Continuous scanner mode
        live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self._on_scan_menu_clicked)

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
        options_action.triggered.connect(self._on_options_menu_clicked)

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Option')
        option_menu.addAction(options_action)

    def _on_scan_menu_clicked(self):
        print("MAIN: Scan menu clicked")
        if not self._camera_capture_alive():
            self._initialise_scanner()

        self._camera_switch.restart_live_capture_from_side()

    def _on_options_menu_clicked(self):
        result_ok = self._open_options_dialog()
        if not result_ok:
            return

        self._cleanup()
        self._initialise_scanner()
        self._camera_switch.restart_live_capture_from_side()

    def _open_options_dialog(self):
        dialog = BarcodeConfigDialog(self._config, self._before_test_camera) # pass the object here and trigger when the button is pressed
        result_ok = dialog.exec_()
        return result_ok

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._cleanup()
        event.accept()

    def _cleanup(self):
        if not self._camera_capture_alive():
            return

        self._camera_scanner.kill()
        self._camera_scanner = None
        self._camera_switch = None

    def _initialise_scanner(self):
        self._camera_scanner = CameraScanner(self._result_queue, self._view_queue, self._message_queue, self._config)
        self._camera_switch = CameraSwitch(self._camera_scanner, self._config.top_camera_timeout)

    def on_record_table_clicked(self):
        if self._camera_capture_alive():
            self._camera_switch.stop_live_capture()

    def _before_test_camera(self):
        # We need to stop the cameras otherwise the Test Camera button won't be able to open them
        self._cleanup()

    def _camera_capture_alive(self):
        return self._camera_scanner is not None and self._camera_switch is not None

    def _read_view_queue(self):
        if not self._view_queue.empty():
            try:
                image = self._view_queue.get(False)
                self.imageFrame.display_puck_image(image)
            except queue.Empty:
                pass

    def _read_message_queue(self):
        if not self._message_queue.empty():
            try:
                message = self._message_queue.get(False)
                print("******************************************************" + message)
            except queue.Empty:
                pass

    def _read_result_queue(self):
        """ Called every second; read any new results from the scan results queue, store them and display them.
        """
        if not self._camera_capture_alive():
            return

        if self._camera_switch.is_side():
            self._read_side_scan()
        else:
            self._read_top_scan()

    def _read_side_scan(self):
        if self._result_queue.empty():
            return

        # Get the result
        plate, holder_image = self._result_queue.get(False)
        if not plate.is_full_valid():
            return

        # Barcode successfully read
        Beeper.beep()
        print("MAIN: side barcode recorded")
        if self.recordTable.unique_side_barcode(plate): # if new side barcode
            self._camera_switch.restart_live_capture_from_top()
            self.original_plate = plate
            self._latest_holder_image = holder_image

    def _read_top_scan(self):
        if self._result_queue.empty():
            if self._camera_switch.is_top_scan_timeout():
                print("\n*** Scan timeout ***")
                self._camera_switch.restart_live_capture_from_side()
            return

        # Get the result
        plate, pins_image = self._result_queue.get(False)

        # Add new record to the table - side is the original_plate read first, top is the plate
        self.recordTable.add_record_frame(self.original_plate, plate, self._latest_holder_image, pins_image)
        if not plate.is_full_valid():
            return

        # Barcodes successfully read
        Beeper.beep()
        print("Scan Recorded")
        self._camera_switch.restart_live_capture_from_side()

