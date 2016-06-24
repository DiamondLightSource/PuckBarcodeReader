from __future__ import division

import pyperclip

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget

from dls_barcode.datamatrix import BAD_DATA_SYMBOL
from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL
from dls_barcode.util import Image, Color


class BarcodeTable(QGroupBox):

    def __init__(self):
        super(BarcodeTable, self).__init__()

        self._barcodes = []

        self.setTitle("Barcodes")
        self._init_ui()

    def _init_ui(self):
        # Create record table - lists all the records in the store
        self._table = QTableWidget()

        # Create barcode table - lists all the barcodes in a record
        self._table = QtGui.QTableWidget()
        self._table.setFixedWidth(110)
        self._table.setFixedHeight(600)
        self._table.setColumnCount(1)
        self._table.setRowCount(10)
        self._table.setHorizontalHeaderLabels(['Barcode'])
        self._table.setColumnWidth(0, 100)

        # Clipboard button - copy the selected barcodes to the clipboard
        self._btn_clipboard = QtGui.QPushButton('Copy To Clipboard')
        self._btn_clipboard.setToolTip('Copy barcodes for the selected record to the clipboard')
        self._btn_clipboard.resize(self._btn_clipboard.sizeHint())
        self._btn_clipboard.clicked.connect(self.copy_selected_to_clipboard)
        self._btn_clipboard.setEnabled(False)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self._btn_clipboard)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self._table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def populate(self, barcodes):
        """ Called when a new row is selected on the record table. Displays all of the
        barcodes from the selected record in the barcode table. Valid barcodes are
        highlighted green, invalid barcodes are highlighted red, and empty slots are grey.
        """
        num_slots = len(barcodes)
        self._table.clearContents()
        self._table.setRowCount(num_slots)

        for index, barcode in enumerate(barcodes):
            # Select appropriate background color
            if barcode == BAD_DATA_SYMBOL:
                color = Color.Red()
            elif barcode == NOT_FOUND_SLOT_SYMBOL:
                color = Color.Red()
            elif barcode == EMPTY_SLOT_SYMBOL:
                color = Color.Grey()
            else:
                color = Color.Green()

            color.a = 192

            # Set table item
            barcode = QtGui.QTableWidgetItem(barcode)
            barcode.setBackgroundColor(color.to_qt())
            barcode.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self._table.setItem(index, 0, barcode)

        self._barcodes = barcodes[:]
        for i, barcode in enumerate(self._barcodes):
            if barcode in [BAD_DATA_SYMBOL, NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL]:
                self._barcodes[i] = ""

        self._update_button_state()

    def _update_button_state(self):
        if self._barcodes is None or len(self._barcodes) == 0:
            self._btn_clipboard.setEnabled(False)
        else:
            self._btn_clipboard.setEnabled(True)

    def copy_selected_to_clipboard(self):
        """ Called when the copy to clipboard button is pressed. Copies the list/s of
        barcodes for the currently selected records to the clipboard so that the user
        can paste it elsewhere.
        """

        if self._barcodes:
            pyperclip.copy('\n'.join(self._barcodes))
