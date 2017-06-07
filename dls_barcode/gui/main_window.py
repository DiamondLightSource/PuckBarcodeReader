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

        self._flag_side = True

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
            # Timer that controls how often new scan results are looked for
            self._result_timer = QtCore.QTimer()
            self._result_timer.timeout.connect(self._read_new_scan_queue)
            self._result_timer.start(1000)
            self._start_live_capture()


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

        #self._btn_begin = QPushButton("Start Scan")
        #self._btn_begin.setStyleSheet("font-size:20pt;")
        #self._btn_begin.setFixedSize(150, 60)
        #self._btn_begin.clicked.connect(self._start_live_capture)

        #open options first to make sure the cameras are set up correctly.
        #start live capture of the side as soon as the dialog box is closed
        dialog = self._open_options_dialog()

        #self._btn_stop = QPushButton("Stop Scan")
        #self._btn_stop.setStyleSheet("font-size:20pt")
        #self._btn_stop.setFixedSize(150, 60)
        #self._btn_stop.clicked.connect(self._stop_live_capture)

        #hbox_btn = QHBoxLayout()
        #hbox_btn.addWidget(self._btn_begin)
        #hbox_btn.addWidget(self._btn_stop)
        #hbox_btn.addStretch()

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

#        vbox.addLayout(hbox_btn)
        vbox.addLayout(hbox)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()

        return dialog


    def init_menu_bar(self):
        """Create and populate the menu bar.
        """
        # Load from file action
        load_action = QtGui.QAction(QtGui.QIcon('open.png'), '&From File...', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load image from file to scan')
        load_action.triggered.connect(self._scan_file_image)

        # Continuous scanner mode
        #live_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Camera Capture', self)
        #live_action.setShortcut('Ctrl+W')
        #live_action.setStatusTip('Capture continuously from camera')
        #live_action.triggered.connect(self._start_live_capture)

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
        options_action.triggered.connect(self._stop_live_capture)
        options_action.triggered.connect(self._start_live_capture)#find a better way of doing this

        # Create menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(exit_action)

  #      scan_menu = menu_bar.addMenu('&Scan')
 #       scan_menu.addAction(load_action)
#        scan_menu.addAction(live_action)

        option_menu = menu_bar.addMenu('&Option')
        option_menu.addAction(options_action)

    def _open_options_dialog(self):
        dialog = BarcodeConfigDialog(self._config, self._camera_config)#pass the object here and trigger when the button is pressed
        dialog.exec_()
        return dialog

    def _read_new_scan_queue(self):
        """ Called every second; read any new results from the scan results queue,
        store them and display them.
        """

        if not self._new_scan_queue.empty():
            # Get the result
            plate, cv_image = self._new_scan_queue.get(False)

            self.imageFrame.display_puck_image(cv_image)

            #TODO:marge images
            # Store scan results and display in GUI
            if self.original_plate != None:
                # new_image = self.original_cv_image.mage_cv_ima ge(cv_image)
                self.recordTable.add_record_frame(self.original_plate, plate, cv_image) # add new record to the table - side is the original_plate read first, top is the palate
            if plate.is_full_valid() and plate._geometry.TYPE_NAME == 'None': # side barcode is successfully read
                # Notify user of new scan
                print("Scan Recorded")
                winsound.Beep(4000, 500)  # frequency, duration
                if self.recordTable.unique_side_barcode(plate): #if new side barcode
                    self._stop_live_capture()
                    self._flag_side = False
                    self._start_live_capture() #start reading the top
                    self.original_plate = plate
                    self.original_cv_image = cv_image#for margeing
            if plate.is_full_valid() and plate._geometry.TYPE_NAME == 'Unipuck':  #top (unipuck) successfully read
                print("Scan wwwwwwwwwwwww Recorded")
                winsound.Beep(4000, 500)  # frequency, duration
                self._stop_live_capture() #stop reading the top
                self._start_live_capture() #start reading side

    def _start_live_capture(self):
        """ Starts the process of continuous capture from an attached camera.
        """
        if (self._flag_side):

            self._scanner = CameraScanner(self._new_scan_queue)

            self._scanner.stream_camera(config=self._config, camera_config = self._camera_config.getSideCameraConfig())

        else:

            self._scanner = CameraScanner(self._new_scan_queue)

            self._scanner.stream_camera(config=self._config, camera_config=self._camera_config.getPuckCameraConfig())



    def _stop_live_capture(self):
        if self._scanner is not None:
            self._scanner.kill()
            self._scanner = None
            self.original_plate = None
            self.original_cv_image = None
            self._flag_side = True




    def _scan_file_image(self):
        """Load and process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file'))
        if filepath:
            cv_image = Image.from_file(filepath)
            gray_image = cv_image.to_grayscale()

            # Scan the image for barcodes
            plate_type = self._config.plate_type.value()
            barcode_size = self._config.barcode_size.value()
            SlotScanner.DEBUG = self._config.slot_images.value()
            SlotScanner.DEBUG_DIR = self._config.slot_image_directory.value()

            if plate_type == "None":
                scanner = OpenScanner(barcode_size)
            else:
                scanner = GeometryScanner(plate_type, barcode_size)

            scan_result = scanner.scan_next_frame(gray_image, is_single_image=True)
            plate = scan_result.plate()

            # If the scan was successful, store the results
            if plate is not None:
                self.recordTable.add_record(plate, None, cv_image)
            else:
                error = "There was a problem scanning the image:\n{}".format(scan_result.error())
                QtGui.QMessageBox.warning(self, "Scanning Error", error)