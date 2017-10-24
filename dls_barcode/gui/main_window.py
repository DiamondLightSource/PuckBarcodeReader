import multiprocessing
import queue
import time

from PyQt4 import QtGui, QtCore

from dls_barcode.config import BarcodeConfig, BarcodeConfigDialog
from dls_barcode.camera import CameraScanner, CameraSwitch, NoNewBarcodeMessage
from dls_util import Beeper
from dls_util.file import FileManager
from .barcode_table import BarcodeTable
from .image_frame import ImageFrame
from .record_table import ScanRecordTable
from .message_box import MessageBox
from .message_factory import MessageFactory


RESULT_TIMER_PERIOD = 1000 # ms
VIEW_TIMER_PERIOD = 1 # ms
MESSAGE_TIMER_PERIOD = 1 # ms


class DiamondBarcodeMainWindow(QtGui.QMainWindow):
    """ Main GUI window for the Barcode Scanner App.
    """
    def __init__(self, config_file, version):
        super(DiamondBarcodeMainWindow, self).__init__()

        self._config = BarcodeConfig(config_file, FileManager())
        self._version = version

        # UI elements
        self._record_table = None
        self._barcode_table = None
        self._image_frame = None

        # Scan elements
        self._camera_scanner = None
        self._camera_switch = None

        self._init_ui()

        # Queue that holds new results generated in continuous scanning mode
        self._result_queue = multiprocessing.Queue()
        self._view_queue = multiprocessing.Queue()
        self._message_queue = multiprocessing.Queue()
        self._initialise_scanner()
        self._reset_msg_timer()

        # Timer that controls how often new scan results are looked for
        self._result_timer = QtCore.QTimer()
        self._result_timer.timeout.connect(self._read_result_queue)
        self._result_timer.start(RESULT_TIMER_PERIOD)

        self._view_timer = QtCore.QTimer()
        self._view_timer.timeout.connect(self._read_view_queue)
        self._view_timer.start(VIEW_TIMER_PERIOD)

        self._message_timer = QtCore.QTimer()
        self._message_timer.timeout.connect(self._read_message_queue)
        self._message_timer.start(MESSAGE_TIMER_PERIOD)

        self._restart_live_capture_from_side()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self._init_icons()

        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(self._window_icon)

        self.init_menu_bar()

        # Barcode table - lists all the barcodes in a record
        self._barcode_table = BarcodeTable(self._config)

        # Image frame - displays image of the currently selected scan record
        self._image_frame = ImageFrame(500, 500, "Plate Image")

        # Scan record table - lists all the records in the store
        self._record_table = ScanRecordTable(self._barcode_table, self._image_frame, self._config, self.on_record_table_clicked)

        # Message display
        self._message_box = MessageBox()
        self._message_box.setFixedHeight(64)

        # Open options first to make sure the cameras are set up correctly.
        # Start live capture of the side as soon as the dialog box is closed
        self._open_options_dialog()

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self._record_table)
        hbox.addWidget(self._barcode_table)

        img_vbox = QtGui.QVBoxLayout()
        img_vbox.addWidget(self._image_frame)
        img_vbox.addWidget(self._message_box)
        hbox.addLayout(img_vbox)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()

    def _init_icons(self):
        self._window_icon = QtGui.QIcon("..\\resources\\icons\\qr_code_32.png")
        self._start_capture_icon = self.style().standardIcon(QtGui.QStyle.SP_MediaPlay)
        self._exit_icon = self.style().standardIcon(QtGui.QStyle.SP_DialogCloseButton)
        self._config_icon = self.style().standardIcon(QtGui.QStyle.SP_FileDialogDetailedView)
        self._about_icon = self.style().standardIcon(QtGui.QStyle.SP_FileDialogInfoView)

    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # Continuous scanner mode
        live_action = QtGui.QAction(self._start_capture_icon, '&Camera Capture', self)
        live_action.setShortcut('Ctrl+W')
        live_action.setStatusTip('Capture continuously from camera')
        live_action.triggered.connect(self._on_scan_action_clicked)

        # Exit Application
        exit_action = QtGui.QAction(self._exit_icon, '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self._cleanup)
        exit_action.triggered.connect(QtGui.qApp.quit)

        # Open options dialog
        options_action = QtGui.QAction(self._config_icon, '&Config', self)
        options_action.setShortcut('Ctrl+O')
        options_action.setStatusTip('Open Options Dialog')
        options_action.triggered.connect(self._on_options_action_clicked)

        # Show version number
        about_action = QtGui.QAction(self._about_icon, "About", self)
        about_action.triggered.connect(self._on_about_action_clicked)

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Options')
        option_menu.addAction(options_action)

        help_menu = menu_bar.addMenu('?')
        help_menu.addAction(about_action)

    def _on_about_action_clicked(self):
        QtGui.QMessageBox.about(self, 'About', "Version: " + self._version)

    def _on_scan_action_clicked(self):
        print("MAIN: Scan menu clicked")
        if not self._camera_capture_alive():
            self._initialise_scanner()

        self._restart_live_capture_from_side()

    def _on_options_action_clicked(self):
        result_ok = self._open_options_dialog()
        if not result_ok:
            return

        self._cleanup()
        self._initialise_scanner()
        self._restart_live_capture_from_side()

    def _open_options_dialog(self):
        dialog = BarcodeConfigDialog(self._config, self._before_test_camera)
        dialog.setWindowIcon(self._config_icon)
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
        if self._view_queue.empty():
            return

        try:
            image = self._view_queue.get(False)
        except queue.Empty:
            return

        self._image_frame.display_puck_image(image)

    def _read_message_queue(self):
        if self._message_queue.empty():
            return

        try:
            scanner_msg = self._message_queue.get(False)
        except queue.Empty:
            return

        if self._camera_switch.is_side() and isinstance(scanner_msg, NoNewBarcodeMessage):
            if not self._msg_timer_is_running():
                # The result queue is read at a slower rate - use a timer to give it time to process a new barcode
                self._start_msg_timer()
            elif self._has_msg_timer_timeout():
                self._message_box.display(MessageFactory.latest_barcode_message())
        else:
            self._reset_msg_timer()
            self._message_box.display(MessageFactory.from_scanner_message(scanner_msg))

    def _reset_msg_timer(self):
        self._duplicate_record_msg_timer = None

    def _start_msg_timer(self):
        self._duplicate_record_msg_timer = time.time()

    def _msg_timer_is_running(self):
        return self._duplicate_record_msg_timer is not None

    def _has_msg_timer_timeout(self):
        timeout = 2 * RESULT_TIMER_PERIOD / 1000
        return self._msg_timer_is_running() and time.time() - self._duplicate_record_msg_timer > timeout

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
        print("MAIN: puck barcode recorded")
        if not self._record_table.is_latest_holder_barcode(plate):
            self._latest_holder_plate = plate
            self._latest_holder_image = holder_image
            self._message_box.display(MessageFactory.puck_recorded_message())
            self._restart_live_capture_from_top()
        else:
            self._message_box.display(MessageFactory.latest_barcode_message())

    def _read_top_scan(self):
        if self._result_queue.empty():
            if self._camera_switch.is_top_scan_timeout():
                self._message_box.display(MessageFactory.scan_timeout_message())
                print("\n*** Scan timeout ***")
                self._restart_live_capture_from_side()
            return

        # Get the result
        plate, pins_image = self._result_queue.get(False)

        # Add new record to the table - side is the _latest_holder_plate read first, top is the plate
        self._record_table.add_record_frame(self._latest_holder_plate, plate, self._latest_holder_image, pins_image)
        if not plate.is_full_valid():
            return

        # Barcodes successfully read
        Beeper.beep()
        print("Scan Completed")
        self._message_box.display(MessageFactory.scan_completed_message())
        self._restart_live_capture_from_side()

    def _restart_live_capture_from_top(self):
        self._camera_switch.restart_live_capture_from_top()

    def _restart_live_capture_from_side(self):
        self._reset_msg_timer()
        self._camera_switch.restart_live_capture_from_side()

