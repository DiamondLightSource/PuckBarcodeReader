import multiprocessing

from dls_barcode.config.barcode_config import CameraConfig
from dls_barcode.data_store.record import Record
from dls_barcode.geometry import GeometryException
from dls_barcode.geometry.exception import GeometryAlignmentError
from dls_barcode.plate import Plate
from dls_barcode.plate.geometry_adjuster import GeometryAdjustmentError
from dls_barcode.scan.with_geometry.scan import NoBarcodesError

try:
    import winsound
except ImportError:
    import os
    def playsound(frequency,duration):
        #apt-get install beep
        os.system('beep -f %s -l %s' % (frequency,duration))
else:
    def playsound(frequency,duration):
        winsound.Beep(frequency,duration)

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QPushButton, QHBoxLayout

from dls_barcode.camera import CameraScanner
from dls_barcode.config import BarcodeConfig, BarcodeConfigDialog
from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_util.image import Image
from .barcode_table import BarcodeTable
from .image_frame import ImageFrame
from .record_table import ScanRecordTable
from dls_barcode.geometry import Geometry

import cv2

class DiamondBarcodeMainWindow(QtGui.QMainWindow):
    """ Main GUI window for the Barcode Scanner App.
    """
    def __init__(self, config_file):
        super(DiamondBarcodeMainWindow, self).__init__()

        self._config = BarcodeConfig(config_file)

        self._camera_config = CameraConfig(config_file)

        self._scanner = None

        # UI elements
        self.recordTable = None
        self.barcodeTable = None
        self.sideBarcodeWindow = None
        self.imageFrame = None
        self.original_plate = None
        self.original_cv_image = None

        dialog = self._init_ui()

        if not dialog.isVisible():
            # Queue that holds new results generated in continuous scanning mode
            self._new_scan_queue = multiprocessing.Queue()
            self._view_queue = multiprocessing.Queue()
            # Timer that controls how often new scan results are looked for
            self._result_timer = QtCore.QTimer()
            self._result_timer.timeout.connect(self._read_new_scan_queue)
            self._result_timer.start(1000)

            self._result_timer1 = QtCore.QTimer()
            self._result_timer1.timeout.connect(self._read_view_queue)
            self._result_timer1.start(1)

            self._start_live_capture(is_side=True)


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

        #open options first to make sure the cameras are set up correctly.
        #start live capture of the side as soon as the dialog box is closed
        dialog = self._open_options_dialog()

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.recordTable)
        hbox.addWidget(self.barcodeTable)
        vbox_new = QtGui.QVBoxLayout()
        vbox_new.addWidget(self.imageFrame)
        hbox_new = QtGui.QHBoxLayout()

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
        live_action.triggered.connect(self._restart_live_capture_from_side)

        # Exit Application
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self._stop_live_capture)
        exit_action.triggered.connect(QtGui.qApp.quit)

        # Open options dialog
        options_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Options', self)
        options_action.setShortcut('Ctrl+O')
        options_action.setStatusTip('Open Options Dialog')
        options_action.triggered.connect(self._open_options_dialog)
        options_action.triggered.connect(self._restart_live_capture_from_side) #find a better way of doing this

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

        scan_menu = menu_bar.addMenu('&Scan')
        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Option')
        option_menu.addAction(options_action)

    def _open_options_dialog(self):
        dialog = BarcodeConfigDialog(self._config, self._camera_config) #pass the object here and trigger when the button is pressed
        dialog.exec_()
        return dialog

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._stop_live_capture()
        event.accept()

    def _read_view_queue(self):
        if not self._view_queue.empty():
            image = self._view_queue.get(False)
            self.imageFrame.display_puck_image(image)

    def _read_new_scan_queue(self):
        """ Called every second; read any new results from the scan results queue,
        store them and display them.
        """
        if not self._new_scan_queue.empty():
            # Get the result
            plate, cv_image = self._new_scan_queue.get(False)
            #self.imageFrame.display_puck_image(cv_image)

            #TODO:merge images
            # Store scan results and display in GUI
            if self.original_plate != None:
                # new_image = self.original_cv_image.mage_cv_ima ge(cv_image)
                self.recordTable.add_record_frame(self.original_plate, plate, cv_image) # add new record to the table - side is the original_plate read first, top is the palate
            if plate.is_full_valid() and plate._geometry.TYPE_NAME == 'None': # side barcode is successfully read
                # Notify user of new scan
                #print("Side Recorded")
                winsound.Beep(4000, 500)  # frequency, duration
                if self.recordTable.unique_side_barcode(plate): #if new side barcode
                    self._restart_live_capture_from_top()
                    self.original_plate = plate
                    self.original_cv_image = cv_image # for merging
            if plate.is_full_valid() and plate._geometry.TYPE_NAME == 'Unipuck':  # top (unipuck) successfully read
                print("Scan Recorded")
                winsound.Beep(4000, 500)  # frequency, duration
                self._restart_live_capture_from_side()

    def _start_live_capture(self, is_side):
        """ Starts the process of continuous capture from an attached camera.
        """
        if (is_side):
            self._scanner = CameraScanner(self._new_scan_queue, self._view_queue)
            self._scanner.stream_camera(config=self._config, camera_config = self._camera_config.getSideCameraConfig())
        else:
            self._scanner = CameraScanner(self._new_scan_queue, self._view_queue)
            self._scanner.stream_camera(config=self._config, camera_config=self._camera_config.getPuckCameraConfig())

    def _stop_live_capture(self):
        if self._scanner is not None:
            self._scanner.kill()
            self._scanner = None
            self.original_plate = None
            self.original_cv_image = None

    def _restart_live_capture_from_side(self):
        self._stop_live_capture()
        self._start_live_capture(True)

    def _restart_live_capture_from_top(self):
        self._stop_live_capture()
        self._start_live_capture(False)

