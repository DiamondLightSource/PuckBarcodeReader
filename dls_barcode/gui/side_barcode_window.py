from __future__ import division

import os

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QHBoxLayout, QTextEdit

from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL


class SideBarcodeWindow(QGroupBox):
    """ GUI component. Displays a list of barcodes for the currently selected puck.
    """
    def __init__(self, options):
        super(SideBarcodeWindow, self).__init__()

        self._barcode = None

        self._options = options

        self.setTitle("Side Barcode")
        self._init_ui()

    def _init_ui(self):
        # Create record table - lists all the records in the store
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFixedHeight(30)
        text.setFixedWidth(110)
        self._text = text

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self._text)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def populate(self, barcode):
        """ Called when a new row is selected on the record table. Displays all of the
        barcodes from the selected record in the barcode table. By default, valid barcodes are
        highlighted green, invalid barcodes are highlighted red, and empty slots are grey.
        """
        self._text.clearContents()

        # Select appropriate background color
        if barcode == NOT_FOUND_SLOT_SYMBOL:
            color = self._options.col_bad()
        elif barcode == EMPTY_SLOT_SYMBOL:
            color = self._options.col_empty()
        else:
            color = self._options.col_ok()

        color.a = 192

        barcode = QtGui.QTextEdit(barcode)
        barcode.setBackgroundColor(color.to_qt())
        barcode.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self._text.setItem(barcode)

        if barcode in [NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL]:
            self._barcode = ""
