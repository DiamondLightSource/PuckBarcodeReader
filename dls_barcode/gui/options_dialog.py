import sys
import os
import subprocess

from PyQt4 import QtGui
from PyQt4.QtGui import QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QMessageBox
from PyQt4.QtCore import Qt, QEvent

from dls_barcode.util.image import Image


class Options:
    def __init__(self):
        self.colour_ok = Image.GREEN
        self.color_not_found = Image.RED
        self.color_unreadable = Image.ORANGE

        self.store_file = ""

        self.slot_images = False
        self.slot_image_directory = ""


class OptionsDialog(QtGui.QDialog):

    def __init__(self, options):
        super(OptionsDialog, self).__init__()

        self.options = options

        self._init_ui()

    def _init_ui(self):
        """ Create the basic elements of the user interface.
        """
        self.setGeometry(100, 100, 350, 400)
        self.setWindowTitle('Options')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        # Message
        lbl_explanation = QLabel("Note that the options in this dialog are not "
                                 "currently saved when the program is closed.")
        lbl_explanation.setStyleSheet("color:red;")

        # Slot scan debug output
        self.chk_slot_debug = QCheckBox("Save images of failed slot scans")
        self.chk_slot_debug.stateChanged.connect(self._slot_debug_clicked)
        self.chk_slot_debug.setTristate(False)
        state = 2 if self.options.slot_images else 0
        self.chk_slot_debug.setCheckState(state)

        btn_show_slot_files = QtGui.QPushButton('View Slot Image Files')
        btn_show_slot_files.setFixedWidth(200)
        btn_show_slot_files.clicked.connect(self._open_slot_image_files_dir)

        grp_debug = QGroupBox("Debugging Output")
        grp_debug_vbox = QVBoxLayout()
        grp_debug_vbox.addWidget(self.chk_slot_debug)
        grp_debug_vbox.addWidget(btn_show_slot_files)
        grp_debug_vbox.addStretch()
        grp_debug.setLayout(grp_debug_vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(lbl_explanation)
        vbox.addSpacing(10)
        vbox.addWidget(grp_debug)

        self.setLayout(vbox)

    def getColorFromDialog(self):
        col = QtGui.QColorDialog.getColor()

        if col.isValid():
            print(col)

    def _slot_debug_clicked(self):
        self.options.slot_images = (self.chk_slot_debug.checkState() != 0)

    def _open_slot_image_files_dir(self):
        path = self.options.slot_image_directory
        path = os.path.abspath(path)

        if sys.platform == 'win32':
            try:
                os.startfile(path)
            except FileNotFoundError:
                QMessageBox.critical(self, "File Error", "Unable to find directory: '{}".format(path))
        else:
            QMessageBox.critical(self, "File Error", "Only available on Windows")


