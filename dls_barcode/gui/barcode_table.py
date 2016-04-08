from __future__ import division

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QTableWidget

from dls_barcode.datamatrix import BAD_DATA_SYMBOL
from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL
from dls_barcode.util.image import Image


class BarcodeTable(QGroupBox):

    def __init__(self):
        super(BarcodeTable, self).__init__()

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

        vbox = QVBoxLayout()
        vbox.addWidget(self._table)

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
                color = self._qt_color(Image.ORANGE)
            elif barcode == NOT_FOUND_SLOT_SYMBOL:
                color = self._qt_color(Image.RED)
            elif barcode == EMPTY_SLOT_SYMBOL:
                color = self._qt_color(Image.GREY)
            else:
                color = self._qt_color(Image.GREEN)

            # Set table item
            barcode = QtGui.QTableWidgetItem(barcode)
            barcode.setBackgroundColor(color)
            barcode.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self._table.setItem(index, 0, barcode)

    def _qt_color(self, cv_color):
        return QtGui.QColor(cv_color[2], cv_color[1], cv_color[0], 128)