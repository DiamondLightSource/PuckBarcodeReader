from dls_barcode.frame_grabber_controller import FrameGrabberController
from dls_util.beeper import Beeper

import logging

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from dls_barcode.config import BarcodeConfigDialog
from dls_barcode.gui.progress_bar import ProgressBox
from dls_barcode.gui.scan_button import ScanButton

from dls_util.cv.frame import Frame

from .barcode_table import BarcodeTable
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
        
        self._init_ui()

        self._frame_grabber_controller = FrameGrabberController(config, self.displayPuckScanCompleteMessage, 
                                                                self.displayScanTimeoutMessage, self.is_latest_holder_barcode,
                                                                self.startCountdown, self.addRecordFrame, self.clear_frame, self.scanCompleted)


    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self._window_icon = QtGui.QIcon("..\\resources\\icons\\qr_code_32.png")

        self.setGeometry(50, 50, 1500, 950) #950
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
        img_hbox = QtWidgets.QHBoxLayout()
        img_hbox.addWidget(self._holder_frame)
        img_hbox.addWidget(self._image_frame)
        table_vbox.addLayout(img_hbox)
        table_vbox.addWidget(self._scan_button)

        hbox.addLayout(table_vbox)
        hbox.addWidget(self._barcode_table)
    
        img_vbox = QtWidgets.QVBoxLayout()
        img_vbox.addWidget(self._result_frame)
        
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
        self._start_frame_grabber()
        self._menu_bar.about_action_trigerred(self._on_about_action_clicked)
        self._menu_bar.options_action_triggered(self._on_options_action_clicked)
        self._record_table.cell_pressed_action_triggered(self._stop_frame_grabber)

    def _stop_frame_grabber(self):
        self._scan_button.setStartLayout()
        self.resetCountdown()
        self._frame_grabber_controller.kill_grabber_thread()
        
    def _start_frame_grabber(self):
        self._scan_button.setStopLayout()
        self._frame_grabber_controller.start_grabber_thread(self.displayHolderFrame, self.displayPuckFrame, 
                                                            self.displayCameraErrorMessage)      

    def _on_about_action_clicked(self):
        QtWidgets.QMessageBox.about(self, 'About', "Version: " + self._version)

    def _on_scan_action_clicked(self):
        self._log.debug("MAIN: Scan menu clicked")
        if  self._scan_button.is_running():
            self._stop_frame_grabber()
        else: 
            self._start_frame_grabber()

    def _on_options_action_clicked(self):
        self._frame_grabber_controller.kill_grabber_thread()
        dialog = BarcodeConfigDialog(self._config)
        self._stop_frame_grabber()
        dialog.exec_()

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._frame_grabber_controller.kill_grabber_thread()
        event.accept()

    def displayCameraErrorMessage(self):
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Critical)
        message_box.setWindowTitle("Camera Error")
        message_box.setText( MessageFactory.camera_not_found_message().content())
        configure_button = message_box.addButton("Configure", QMessageBox.ActionRole)
        message_box.addButton("Quit", QMessageBox.ActionRole)
        message_box.setEscapeButton(configure_button)
        message_box.exec_()
        if message_box.clickedButton() == configure_button:
            self._on_options_action_clicked()
            self._on_scan_action_clicked()
        else:
            self.close()

    def displayPuckScanCompleteMessage(self):
        if self._config.get_scan_beep():
            Beeper.beep()
        self._message_box.display(MessageFactory.puck_scan_completed_message())

    def clear_frame(self):
        self._result_frame.clear_frame()

    def displayScanTimeoutMessage(self):
        if self._config.get_scan_beep():
            Beeper.beep()
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
        
    def addRecordFrame(self, top_result, side_result):
        holder_barcode = side_result.get_first_barcode().data()
        plate = top_result.plate()
        holder_image = side_result.get_frame_image()
        pins_image = top_result.get_frame_image()
        self._record_table.add_record_frame(holder_barcode, plate, holder_image, pins_image)

    def startCountdown(self, duration):
        self._countdown_box.start_countdown(duration)

    def resetCountdown(self):
        self._countdown_box.reset_countdown()

    def scanCompleted(self):
        self._countdown_box.scan_completed()
        
    def is_latest_holder_barcode(self, result_barcode):
        return self._record_table.is_latest_holder_barcode(result_barcode)
    
    #@pyqtSlot(ScanErrorMessage)
    #def displayScanErrorMessage(self, scanner_msg): 
    #    self._message_box.display(MessageFactory.from_scanner_message(scanner_msg))
    
    #@pyqtSlot(ScanErrorMessage)
    #def clear_frame_display_message(self, scanner_msg):     
    #    self._result_frame.clear_frame_and_set_text(scanner_msg.content())
