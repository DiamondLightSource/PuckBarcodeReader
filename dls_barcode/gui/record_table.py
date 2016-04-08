from __future__ import division

import os
import pyperclip

from PyQt4 import QtGui
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget
from PyQt4.QtCore import Qt

from dls_barcode.image import CvImage
from dls_barcode.gui.store import Store
from dls_barcode.gui import STORE_FILE, STORE_IMAGE_PATH

# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys


class ScanRecordTable(QGroupBox):
    COLUMNS = ['Date', 'Time', 'Plate Type', 'Valid', 'Invalid', 'Empty']

    def __init__(self, barcode_table, image_frame):
        super(ScanRecordTable, self).__init__()

        # Create directory if missing
        if not os.path.exists(STORE_IMAGE_PATH):
            os.makedirs(STORE_IMAGE_PATH)

        # Read the store from file
        self._store = Store.from_file(STORE_FILE)

        self._barcodeTable = barcode_table
        self._imageFrame = image_frame

        self.setTitle("Scan Records")
        self._init_ui()

        self._load_store_records()

    def _init_ui(self):
        # Create record table - lists all the records in the store
        self._table = QTableWidget()
        self._table.setFixedWidth(440)
        self._table.setFixedHeight(600)
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setColumnWidth(0, 70)
        self._table.setColumnWidth(1, 55)
        self._table.setColumnWidth(2, 85)
        self._table.setColumnWidth(3, 60)
        self._table.setColumnWidth(4, 60)
        self._table.setColumnWidth(5, 60)
        self._table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._table.cellPressed.connect(self._record_selected)

        # Delete button - deletes selected records
        deleteBtn = QtGui.QPushButton('Delete')
        deleteBtn.setToolTip('Delete selected scan/s')
        deleteBtn.resize(deleteBtn.sizeHint())
        deleteBtn.clicked.connect(self._delete_selected_records)

        # Clipboard button - copy the selected barcodes to the clipboard
        clipboardBtn = QtGui.QPushButton('Copy To Clipboard')
        clipboardBtn.setToolTip('Copy barcodes for the selected record to the clipboard')
        clipboardBtn.resize(clipboardBtn.sizeHint())
        clipboardBtn.clicked.connect(self._copy_selected_to_clipboard)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(clipboardBtn)
        hbox.addWidget(deleteBtn)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self._table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def add_record(self, plate_type, barcodes, image):
        """ Add a new scan record to the store and display it. """
        self._store.add_record(plate_type, barcodes, image)
        self._load_store_records()

    def _load_store_records(self):
        """ Populate the record table with all of the records in the store.
        """
        self._table.clearContents()
        self._table.setRowCount(self._store.size())

        for n, record in enumerate(self._store.records):
            items = [record.date, record.time, record.plate_type, record.num_valid_barcodes,
                     record.num_invalid_barcodes+record.num_unread_slots, record.num_empty_slots]

            if (record.num_valid_barcodes + record.num_empty_slots) == record.num_slots:
                color = self._qt_color(CvImage.GREEN)
            else:
                color = self._qt_color(CvImage.RED)


            for m, item in enumerate(items):
                newitem = QtGui.QTableWidgetItem(str(item))
                newitem.setBackgroundColor(color)
                newitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self._table.setItem(n, m, newitem)

        # Display the first (most recent) record
        self._table.setCurrentCell(0, 0)
        self._record_selected()

    def _record_selected(self):
        """ Called when a row is selected, causes details of the selected record to be
        displayed (list of barcodes in the barcode table and image of the scan in the
        image frame).
        """
        try:
            row = self._table.selectionModel().selectedRows()[0].row()
            record = self._store.get_record(row)
            self._barcodeTable.populate(record.barcodes)
            self._imageFrame.display_image(record.imagepath)
        except IndexError:
            pass
            self._barcodeTable.populate([])
            self._imageFrame.display_image(None)

    def _delete_selected_records(self):
        """ Called when the 'Delete' button is pressed. Deletes all of the selected records
        (and the associated images) from the store and from disk. Asks for user confirmation.
        """
        # Display a confirmation dialog to check that user wants to proceed with deletion
        quit_msg = "This operation cannot be undone.\nAre you sure you want to delete these record/s?"
        reply = QtGui.QMessageBox.warning(self, 'Confirm Delete',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        # If yes, find the appropriate records and delete them
        if reply == QtGui.QMessageBox.Yes:
            rows = self._table.selectionModel().selectedRows()
            records_to_delete = []
            for row in rows:
                index = row.row()
                record = self._store.get_record(index)
                records_to_delete.append(record)

            self._store.delete_records(records_to_delete)
            self._load_store_records()

    def _copy_selected_to_clipboard(self):
        """ Called when the copy to clipboard button is pressed. Copies the list/s of
        barcodes for the currently selected records to the clipboard so that the user
        can paste it elsewhere.
        """
        rows = self._table.selectionModel().selectedRows()
        rows = sorted([row.row() for row in rows])
        barcodes = []
        for row in rows:
            record = self._store.get_record(row)
            barcodes.extend(record.filtered_barcodes)

        if barcodes:
            pyperclip.copy('\n'.join(barcodes))
        #spam = pyperclip.paste()

    def _qt_color(self, cv_color):
        return QtGui.QColor(cv_color[2], cv_color[1], cv_color[0], 128)