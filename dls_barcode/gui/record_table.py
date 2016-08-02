from __future__ import division

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget

from data_store import Store

# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys


class ScanRecordTable(QGroupBox):
    """ GUI component. Displays a list of previous scan results. Selecting a scan causes
    details of the scan to appear in other GUI components (list of barcodes in the barcode
    table and image of the puck in the image frame).
    """
    COLUMNS = ['Date', 'Time', 'Plate Type', 'Valid', 'Invalid', 'Empty']

    def __init__(self, barcode_table, image_frame, options):
        super(ScanRecordTable, self).__init__()

        # Read the store from file
        self._store = Store(options.store_directory.value(), options)
        self._options = options

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
        btn_delete = QtGui.QPushButton('Delete')
        btn_delete.setToolTip('Delete selected scan/s')
        btn_delete.resize(btn_delete.sizeHint())
        btn_delete.clicked.connect(self._delete_selected_records)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(btn_delete)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self._table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def add_record(self, plate, image):
        """ Add a new scan record to the store and display it. """
        self._store.add_record(plate, image)
        self._load_store_records()

    def add_record_frame(self, plate, image):
        """ Add a new scan frame - creates a new record if its a new puck, else merges with previous record"""
        self._store.merge_record(plate, image)
        self._load_store_records()
        if self._options.scan_clipboard.value():
            self._barcodeTable.copy_selected_to_clipboard()

    def _load_store_records(self):
        """ Populate the record table with all of the records in the store.
        """
        self._table.clearContents()
        self._table.setRowCount(self._store.size())

        for n, record in enumerate(self._store.records):
            items = [record.date, record.time, record.plate_type, record.num_valid_barcodes,
                     record.num_unread_slots, record.num_empty_slots]

            if (record.num_valid_barcodes + record.num_empty_slots) == record.num_slots:
                color = self._options.col_ok()
            else:
                color = self._options.col_bad()

            color.a = 192
            for m, item in enumerate(items):
                new_item = QtGui.QTableWidgetItem(str(item))
                new_item.setBackgroundColor(color.to_qt())
                new_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self._table.setItem(n, m, new_item)

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
            marked_image = record.marked_image(self._options)
            self._imageFrame.display_puck_image(marked_image)
        except IndexError:
            pass
            self._barcodeTable.populate([])
            self._imageFrame.clear_frame()

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
