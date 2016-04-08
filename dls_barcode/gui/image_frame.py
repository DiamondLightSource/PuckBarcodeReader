from __future__ import division

import os
from PyQt4 import QtGui
from PyQt4.QtGui import QLabel, QGroupBox, QVBoxLayout, QHBoxLayout, QWidget, QTableWidget
from PyQt4.QtCore import Qt, QEvent

from dls_barcode.image import CvImage


class ImageFrame(QGroupBox):

    def __init__(self):
        super(ImageFrame, self).__init__()

        self.setTitle("Scan Image")
        self._init_ui()

    def _init_ui(self):
        # Image frame - displays image of the currently selected scan record
        self._frame = QLabel()
        self._frame.setStyleSheet("background-color: black; color: red; font-size: 30pt; text-align: center")
        self._frame.setFixedWidth(600)
        self._frame.setFixedHeight(600)

        vbox = QVBoxLayout()
        vbox.addWidget(self._frame)

        self.setLayout(vbox)

    def display_image(self, filename):
        """ Called when a new row is selected on the record table. Displays the specified
        image (image of the highlighted scan) in the image frame
        """
        self._frame.clear()
        self._frame.setAlignment(Qt.AlignCenter)

        if filename is None:
            self._frame.setText("No Scan Selected")
        elif os.path.isfile(filename):
            pixmap = QtGui.QPixmap(filename)
            self._frame.setPixmap(pixmap.scaled(self._frame.size(),
                                                    Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self._frame.setText("Image Not Found")
