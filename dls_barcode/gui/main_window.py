from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox

from dls_barcode.config import BarcodeConfigDialog
from dls_barcode.gui.progress_bar import ProgressBox
from dls_barcode.gui.scan_button import ScanButton
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
        self._config = config
        self._version = version
        self._cleanup = None
        self._initialise_scanner = None
        self._camera_capture_alive = None

        # UI elements
        self._record_table = None
        self._barcode_table = None
        self._image_frame = None
        self._scan_button = None
        self._countdown_box = None

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
        self._image_frame = ImageFrame("Plate Image")

        # Scan record table - lists all the records in the store
        self._record_table = ScanRecordTable(self._barcode_table, self._image_frame, self._config)

        # Message display
        self._message_box = MessageBox()

        # Count down display
        #self._countdown_box = CountdownBox()
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
        img_vbox.addWidget(self._image_frame)

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

    def set_actions_triger(self, cleanup, cleanup_logging, initialise_scanner, camera_capture_alive):
        self._cleanup = cleanup
        self._cleanup_logging = cleanup_logging
        self._initialise_scanner = initialise_scanner
        self._camera_capture_alive = camera_capture_alive
        self._scan_button.click_action(self._on_scan_action_clicked)
        self._menu_bar.exit_action_triggered(self._cleanup)
        self._menu_bar.about_action_trigerred(self._on_about_action_clicked)
        self._menu_bar.optiones_action_triggered(self._on_options_action_clicked)
        self._record_table.cell_pressed_action_triggered(self._to_run_on_table_clicked)

    def _to_run_on_table_clicked(self):
        self._cleanup()
        self._scan_button.setStartLayout()

    def _on_about_action_clicked(self):
        QtWidgets.QMessageBox.about(self, 'About', "Version: " + self._version)

    def _on_scan_action_clicked(self):
        print("MAIN: Scan menu clicked")
        if not self._camera_capture_alive():
            self._initialise_scanner()
            self._scan_button.setDelayedStopLayout()
        else:
            self._cleanup()
            self._scan_button.setStartLayout()

    def _on_options_action_clicked(self):
        dialog = BarcodeConfigDialog(self._config, self._cleanup)
        self._scan_button.setStartLayout()
        dialog.exec_()

    def closeEvent(self, event):
        """This overrides the method from the base class.
        It is called when the user closes the window from the X on the top right."""
        self._cleanup()
        self._cleanup_logging()
        event.accept()

    def displayScanCompleteMessage(self):
        self._message_box.display(MessageFactory.scan_completed_message())

    def displayPuckScanCompleteMessage(self):
        self._message_box.display(MessageFactory.puck_scan_completed_message())

    def displayCameraErrorMessage(self, scanner_message):
        self._cleanup()
        mgs = QMessageBox(self)
        mgs.setIcon(QMessageBox.Critical)
        mgs.setWindowTitle("Camera Error")
        mgs.setText( scanner_message.content()+" " + MessageFactory.camera_not_found_message().content())
        configure_button = mgs.addButton("Configure", QMessageBox.ActionRole)
        quit_button = mgs.addButton("Quit", QMessageBox.ActionRole)
        mgs.setEscapeButton(configure_button)
        mgs.exec_()
        if mgs.clickedButton() == configure_button:
            self._on_options_action_clicked()
            self._on_scan_action_clicked()
        else:
            self.close()

    def displayScanErrorMessage(self, scanner_msg):
        self._message_box.display(MessageFactory.from_scanner_message(scanner_msg))

    def displayScanTimeoutMessage(self):
        self._message_box.display(MessageFactory.scan_timeout_message())

    def displayPuckImage(self, image):
        self._image_frame.display_puck_image(image)

    def addRecordFrame(self, latest_holder_barcode, plate, latest_holder_image, pins_image):
        self._record_table.add_record_frame(latest_holder_barcode, plate, latest_holder_image, pins_image)

    def isLatestHolderBarcode(self, holder_barcode):
        return self._record_table.is_latest_holder_barcode(holder_barcode)

    def startCountdown(self, count):
        self._countdown_box.start_countdown(count)

    def resetCountdown(self):
        self._countdown_box.reset_countdown()

    def scanCompleted(self):
        self._countdown_box.scan_completed()
