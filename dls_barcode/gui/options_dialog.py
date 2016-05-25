import sys
import os

from PyQt4 import QtGui
from PyQt4.QtGui import QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QMessageBox, QLineEdit
from PyQt4.QtCore import Qt, QEvent

class OptionsDialog(QtGui.QDialog):

    def __init__(self, options):
        super(OptionsDialog, self).__init__()

        self.options = options

        self._init_ui()
        self._update_options_display()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 350, 400)
        self.setWindowTitle('Options')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        LABEL_WIDTH = 100

        # ------ SCANNING OPTIONS -------
        # Set Camera Number
        self.txt_camera_number = QLineEdit()
        self.txt_camera_number.setFixedWidth(30)
        lbl_camera_number = QLabel("Camera Number:")
        lbl_camera_number.setFixedWidth(LABEL_WIDTH)

        hbox_scan_dir = QHBoxLayout()
        hbox_scan_dir.addWidget(lbl_camera_number)
        hbox_scan_dir.addWidget(self.txt_camera_number)
        hbox_scan_dir.addStretch()

        # Set camera resolution
        self.txt_camera_width = QLineEdit()
        self.txt_camera_width.setFixedWidth(50)
        self.txt_camera_height = QLineEdit()
        self.txt_camera_height.setFixedWidth(50)
        lbl_camera_res = QLabel("Camera Resolution:")
        lbl_camera_res.setFixedWidth(LABEL_WIDTH)

        hbox_cam_res = QHBoxLayout()
        hbox_cam_res.addWidget(lbl_camera_res)
        hbox_cam_res.addWidget(self.txt_camera_width)
        hbox_cam_res.addWidget(QLabel("x"))
        hbox_cam_res.addWidget(self.txt_camera_height)
        hbox_cam_res.addStretch()

        grp_scan = QGroupBox("Scanning")
        vbox_grp_scan = QVBoxLayout()
        vbox_grp_scan.addLayout(hbox_scan_dir)
        vbox_grp_scan.addLayout(hbox_cam_res)
        vbox_grp_scan.addStretch()
        grp_scan.setLayout(vbox_grp_scan)

        # ------ STORE OPTIONS --------
        # Set Store Directory
        self.txt_store_dir = QLineEdit()
        lbl_store_dir = QLabel("Store Directory:")
        lbl_store_dir.setFixedWidth(LABEL_WIDTH)

        hbox_store_dir = QHBoxLayout()
        hbox_store_dir.addWidget(lbl_store_dir)
        hbox_store_dir.addWidget(self.txt_store_dir)

        # View Store Directory
        btn_show_store_files = QtGui.QPushButton('View Store Files')
        btn_show_store_files.setFixedWidth(150)
        btn_show_store_files.clicked.connect(self._open_store_files_dir)

        grp_store = QGroupBox("Store")
        vbox_grp_store = QVBoxLayout()
        vbox_grp_store.addLayout(hbox_store_dir)
        vbox_grp_store.addWidget(btn_show_store_files)
        vbox_grp_store.addStretch()
        grp_store.setLayout(vbox_grp_store)

        # ------ DEBUG OPTIONS --------
        # Slot scan debug output
        self.chk_slot_debug = QCheckBox("Save images of failed slot scans")
        self.chk_slot_debug.setTristate(False)
        state = 2 if self.options.slot_images else 0
        self.chk_slot_debug.setCheckState(state)

        # Set slot images directory
        self.txt_slot_files_dir = QLineEdit(self.options.slot_image_directory)
        lbl_slot_files_dir = QLabel("Debug Directory:")
        lbl_slot_files_dir.setFixedWidth(LABEL_WIDTH)
        hbox_debug_dir = QHBoxLayout()
        hbox_debug_dir.addWidget(lbl_slot_files_dir)
        hbox_debug_dir.addWidget(self.txt_slot_files_dir)

        # Show slot images button
        btn_show_slot_files = QtGui.QPushButton('View Slot Image Files')
        btn_show_slot_files.setFixedWidth(150)
        btn_show_slot_files.clicked.connect(self._open_slot_image_files_dir)

        grp_debug = QGroupBox("Debugging Output")
        grp_debug_vbox = QVBoxLayout()
        grp_debug_vbox.addWidget(self.chk_slot_debug)
        grp_debug_vbox.addLayout(hbox_debug_dir)
        grp_debug_vbox.addWidget(btn_show_slot_files)
        grp_debug_vbox.addStretch()
        grp_debug.setLayout(grp_debug_vbox)

        # ----- OK /CANCEL BUTTONS -------
        btn_cancel = QtGui.QPushButton("Cancel")
        btn_cancel.pressed.connect(self._dialog_close_cancel)
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.pressed.connect(self._dialog_close_ok)
        btn_apply = QtGui.QPushButton("Apply")
        btn_apply.pressed.connect(self._dialog_apply_changes)

        hbox_ok_cancel = QtGui.QHBoxLayout()
        hbox_ok_cancel.addStretch(1)
        hbox_ok_cancel.addWidget(btn_cancel)
        hbox_ok_cancel.addWidget(btn_apply)
        hbox_ok_cancel.addWidget(btn_ok)
        hbox_ok_cancel.addStretch(1)

        # ----- MAIN LAYOUT -----
        vbox = QVBoxLayout()
        vbox.addWidget(grp_scan)
        vbox.addWidget(grp_store)
        vbox.addWidget(grp_debug)
        vbox.addStretch()
        vbox.addLayout(hbox_ok_cancel)

        self.setLayout(vbox)

    def _update_options_display(self):
        state = 2 if self.options.slot_images else 0
        self.chk_slot_debug.setCheckState(state)

        self.txt_slot_files_dir.setText(self.options.slot_image_directory)
        self.txt_store_dir.setText(self.options.store_directory)
        self.txt_camera_number.setText(str(self.options.camera_number))
        self.txt_camera_width.setText(str(self.options.camera_width))
        self.txt_camera_height.setText(str(self.options.camera_height))

    def getColorFromDialog(self):
        col = QtGui.QColorDialog.getColor()

        if col.isValid():
            print(col)

    def _open_slot_image_files_dir(self):
        path = self.options.slot_image_directory
        path = os.path.abspath(path)
        self._open_directory(path)

    def _open_store_files_dir(self):
        path = self.options.store_directory
        path = os.path.abspath(path)
        self._open_directory(path)

    def _open_directory(self, abspath):
        if sys.platform == 'win32':
            try:
                os.startfile(abspath)
            except FileNotFoundError:
                QMessageBox.critical(self, "File Error", "Unable to find directory: '{}".format(abspath))
        else:
            QMessageBox.critical(self, "File Error", "Only available on Windows")

    def _dialog_apply_changes(self):
        self.options.slot_images = (self.chk_slot_debug.checkState() != 0)
        self.options.slot_image_directory = self.txt_slot_files_dir.text()
        self.options.store_directory = self.txt_store_dir.text()
        self.options.camera_number = self.txt_camera_number.text()
        self.options.camera_width = self.txt_camera_width.text()
        self.options.camera_height = self.txt_camera_height.text()

        self.options.update_config_file()
        self._update_options_display()

    def _dialog_close_ok(self):
        self._dialog_apply_changes()
        self.close()

    def _dialog_close_cancel(self):
        self.close()


