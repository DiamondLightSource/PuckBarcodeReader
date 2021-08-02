

import logging
import time
from datetime import datetime

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QMutex, QThread, QTimer, pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from dls_barcode.config import BarcodeConfigDialog
from dls_barcode.gui.progress_bar import ProgressBox
from dls_barcode.gui.scan_button import ScanButton
from dls_barcode.scanner_manager import Scanner, Processor, ScannerManager
from dls_barcode.scan import scan_result
from dls_barcode.scan.scan_result import ScanResult
from dls_util.cv.frame import Frame
from dls_util.message import message_type

from .barcode_table import BarcodeTable
from .countdown_box import CountdownBox
from .image_frame import ImageFrame
from .menu_bar import MenuBar
from .message_box import MessageBox
from .message_factory import MessageFactory
from .record_table import ScanRecordTable


class DiamondBarcodeMainWindow(QtWidgets.QMainWindow):
    """ Main GUI window for the Barcode Scanner App.
    """

    def __init__(self, config, version, flags, *args, **kwargs):

        super().__init__(flags, *args, **kwargs)
        self._log = logging.getLogger(".".join([__name__]))

        self._config = config
        self._version = version


        # UI elements
        self._record_table = None
        self._barcode_table = None
        self._image_frame = None
        self._holder_frame = None
        self._result_frame = None
        self._scan_button = None
        self._countdown_box = None
        
        self.main_thread = QThread()
        self.processor_thread = QThread() 
        self._manager = ScannerManager(self._config)
        self._last_barcode = None
        self._duration = self._config.get_top_camera_tiemout()
        self._init_ui()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self._window_icon = QtGui.QIcon("..\\resources\\icons\\qr_code_32.png")

        self.setGeometry(50, 50, 1500, 650) #950
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(self._window_icon)

        self._menu_bar = MenuBar(self.menuBar(), self._version, None)

        # Barcode table - lists all the barcodes in a record
        self._barcode_table = BarcodeTable(self._config)

        # Scan button - start/stop scan
        self._scan_button = ScanButton('Start/stop scan')

        # Image frame - displays image of the currently selected scan record
        self._image_frame = ImageFrame("Plate")
        self._holder_frame = ImageFrame("Holder")
        self._result_frame = ImageFrame("Result")

        # Scan record table - lists all the records in the store
        self._record_table = ScanRecordTable(self._barcode_table, self._image_frame, self._holder_frame, self._result_frame, self._config)

        # Message display
        self._message_box = MessageBox()

        # Count down display
        self._countdown_box = ProgressBox()

        # Create layout

        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(10)

        table_vbox = QtWidgets.QVBoxLayout()
        table_vbox.addWidget(self._record_table)
        table_vbox.addWidget(self._scan_button)

        hbox.addLayout(table_vbox)
        hbox.addWidget(self._barcode_table)
      

        img_vbox = QtWidgets.QVBoxLayout()
        img_vbox.addWidget(self._result_frame)
        
        img_hbox = QtWidgets.QHBoxLayout()
        img_hbox.addWidget(self._holder_frame)
        img_hbox.addWidget(self._image_frame)
        img_vbox.addLayout(img_hbox)

        msg_hbox = QtWidgets.QHBoxLayout()
        msg_hbox.setSpacing(10)
        msg_hbox.addWidget(self._message_box)
        msg_hbox.addWidget(self._countdown_box)

        img_vbox.addLayout(msg_hbox)

        hbox.addLayout(img_vbox)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(vbox)
        self.setCentralWidget(main_widget)

        self.show()

    def set_actions_triger(self):
        self._load_store_records()
        self._scan_button.click_action(self._on_scan_action_clicked)
        self._scan_button.setStopLayout()
        self._start_main_thread() 
        self._menu_bar.about_action_trigerred(self._on_about_action_clicked)
        self._menu_bar.optiones_action_triggered(self._on_options_action_clicked)
        self._record_table.cell_pressed_action_triggered(self._to_run_on_table_clicked)


    def _to_run_on_table_clicked(self):
        self._scan_button.setStartLayout()
        self._kill_main_thread()
    
    def _on_about_action_clicked(self):
        QtWidgets.QMessageBox.about(self, 'About', "Version: " + self._version)

    def _on_scan_action_clicked(self):
        self._log.debug("MAIN: Scan menu clicked")
        if  self._scan_button.is_running():
            self._scan_button.setStartLayout()
            self.resetCountdown()
            self._kill_main_thread()
        else: 
            self._scan_button.setStopLayout()
            self._start_main_thread()      
            
    def _start_main_thread(self):
        self.main_thread = QThread()

        self._manager.initialise_scanner()
        self.main_worker = Scanner(self._manager.side_camera_stream,self._manager.top_camera_stream, self._duration)
        self.main_worker.moveToThread(self.main_thread)
        self.main_thread.started.connect(self.main_worker.run)
        self.main_worker.new_side_frame.connect(self.displayHolderFrame)
        self.main_worker.new_top_frame.connect(self.displayPuckFrame)
        self.main_worker.finished.connect(self.main_worker.deleteLater)   
        self.main_thread.finished.connect(self.main_worker.deleteLater) 
        self.main_worker.finished.connect(self.main_thread.quit)
        self.main_worker.images_collected.connect(self.start_processor)
        self.main_worker.camera_error.connect(self.displayCameraErrorMessage)
        self.main_worker.stop_time_signal.connect(self.displayScanTimeoutMessage)
        self.main_worker.start_time_signal.connect(self.startCountdown)
        self.main_thread.start()
            
    def _kill_main_thread(self):
        self.main_worker.stop() 
        self.main_thread.quit()
        self.main_thread.wait()
        self._manager.cleanup()
              
        
    @pyqtSlot(Frame, Frame)
    def start_processor(self, side_frame, top_frame):    
        if  not self.processor_thread.isRunning():
                self.processor_worker = Processor(self._manager.side_camera_stream, self._manager.top_camera_stream, side_frame, top_frame)
                self.processor_worker.moveToThread(self.processor_thread)
                self.processor_thread.started.connect(self.processor_worker.run)
                self.processor_worker.finished.connect(self.processor_thread.quit)
                self.processor_worker.finished.connect(self.processor_thread.wait)
                self.processor_thread.start()
                self.processor_worker.side_top_result.connect(self.addRecordFrame)
                self.processor_worker.side_result_signal.connect(self.isLatestHolderBarcode)
 
    def _on_options_action_clicked(self):
        self._kill_main_thread()
        dialog = BarcodeConfigDialog(self._config)
        self._scan_button.setStartLayout()
        self.resetCountdown()
        dialog.exec_()
       
    @pyqtSlot(ScanResult)
    def isLatestHolderBarcode(self, result):
        if self._last_barcode is None:
            self._last_barcode = result.barcodes()[0].data()
        
        if result.barcodes()[0].data() != self._last_barcode:
            self._last_barcode = result.barcodes()[0].data()

            self.main_worker.set_new_side_code()
            

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._kill_main_thread()
        event.accept()

    def displayCameraErrorMessage(self):
        mgs = QMessageBox(self)
        mgs.setIcon(QMessageBox.Critical)
        mgs.setWindowTitle("Camera Error")
        mgs.setText( MessageFactory.camera_not_found_message().content())
        configure_button = mgs.addButton("Configure", QMessageBox.ActionRole)
        mgs.addButton("Quit", QMessageBox.ActionRole)
        mgs.setEscapeButton(configure_button)
        mgs.exec_()
        if mgs.clickedButton() == configure_button:
            self._on_options_action_clicked()
            self._on_scan_action_clicked()
        else:
            self.close()

    def displayPuckScanCompleteMessage(self):
        self._message_box.display(MessageFactory.puck_scan_completed_message())
    
    def displayScanErrorMessage(self, scanner_msg): # not sure when should it be displayed 
        self._message_box.display(MessageFactory.from_scanner_message(scanner_msg))

    def displayScanTimeoutMessage(self):
        self._message_box.display(MessageFactory.scan_timeout_message())



    @pyqtSlot(Frame)
    def displayPuckFrame(self, frame):
        if frame is None:
            return
        self._image_frame.display_image(frame.frame_to_image())
    
    @pyqtSlot(Frame)
    def displayHolderFrame(self, frame):
        if frame is None:
            return
        self._holder_frame.display_image(frame.frame_to_image())

    def _load_store_records(self):
        self._record_table._load_store_records()
    
    @pyqtSlot(ScanResult, ScanResult)
    def addRecordFrame(self, side_result, top_result):
        latest_holder_barcode = side_result.barcodes()[0].data()
       # print('side OK' + latest_holder_barcode)
        #print(top_result.success())
        if  top_result.success() and latest_holder_barcode != '':
            #print("adding result")
            plate = top_result.plate()
            latest_holder_image = side_result.get_frame_image()
            pins_image = top_result.get_frame_image()
            self._record_table.add_record_frame(latest_holder_barcode, plate, latest_holder_image, pins_image)
  

    def startCountdown(self):
        self._countdown_box.start_countdown(self._duration)

    def resetCountdown(self):
        self._countdown_box.reset_countdown()

    def scanCompleted(self):
        self._countdown_box.scan_completed()
        
    
