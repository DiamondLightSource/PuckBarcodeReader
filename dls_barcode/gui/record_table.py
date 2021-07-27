from __future__ import division

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget, QMessageBox

from dls_barcode.data_store import Store
from dls_barcode.data_store.store_loader import StoreLoader
from dls_barcode.data_store.store_writer import StoreWriter

# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys


class ScanRecordTable(QGroupBox):
    """ GUI component. Displays a list of previous scan results. Selecting a scan causes
    details of the scan to appear in other GUI components (list of barcodes in the barcode
    table and image of the puck in the image frame).
    """
    COLUMNS = ['Date', 'Time', 'Plate Barcode', 'Valid', 'Invalid', 'Empty', 'Plate Type']

    def __init__(self, barcode_table, image_frame, holder_frame, result_frame, options):
        super(ScanRecordTable, self).__init__()

        # Read the store from file
        store_writer = StoreWriter(options.get_store_directory(), "store")
        store_loader = StoreLoader(options.get_store_directory(), "store")

        self._store = Store(store_writer, store_loader.load_records_from_file())
        self._options = options

        self._barcodeTable = barcode_table
        self._imageFrame = image_frame
        self._holderFrame = holder_frame
        self._resultFrame = result_frame

        self.setTitle("Scan Records")
        self.setMaximumWidth(730)

        self._init_ui()

    def _init_ui(self):
        # Create record table - lists all the records in the store
        self._table = QTableWidget()
        self._table.setMinimumWidth(720) #900
        self._table.setMinimumHeight(600)
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)

        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)


        # Delete button - deletes selected records
        btn_delete = QtWidgets.QPushButton('Delete')
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

    def cell_pressed_action_triggered(self, to_run_on_table_clicked):
        self._table.cellPressed.connect(to_run_on_table_clicked)
        self._table.cellPressed.connect(self._record_selected)

    def add_record_frame(self, holder_barcode, plate, holder_img, pins_img):
        """ Add a new scan frame - creates a new record if its a new puck, else merges with previous record"""
        self._store.merge_record(holder_barcode, plate, holder_img, pins_img)
        self._load_store_records()
        if self._options.scan_clipboard.value():
            self._barcodeTable.copy_to_clipboard()

    def _load_store_records(self):
        """ Populate the record table with all of the records in the store.
        """
        self._table.clearContents()
        self._table.setRowCount(self._store.size())

        for n, record in enumerate(self._store.records):
            items = [record.date, record.time, record.holder_barcode, record.num_valid_barcodes,
                     record.num_unread_slots, record.num_empty_slots, record.plate_type]
            valid_empty = record.num_valid_barcodes + record.num_empty_slots
            if valid_empty == record.num_slots:
                color = self._options.col_ok()
            elif valid_empty < record.num_slots and record.num_valid_barcodes > 0:
                color = self._options.col_accept()
            else:
                color = self._options.col_bad()

            color.a = 192
            for m, item in enumerate(items):
                new_item = QtWidgets.QTableWidgetItem(str(item))
                new_item.setBackground(color.to_qt())
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
            # Clear all events
            QtWidgets.QApplication.processEvents()
            row = self._table.selectionModel().selectedRows()[0].row()
            record = self._store.get_record(row)
            self._barcodeTable.populate(record.holder_barcode, record.barcodes)
            marked_image = record.get_marked_image(self._options)
            image = record.get_image()
            holder_image = record.get_holder_image()
            self._imageFrame.display_image(image)
            self._holderFrame.display_image(holder_image)
            self._resultFrame.display_image(marked_image)
        except IndexError:
            self._barcodeTable.clear()
#            self._imageFrame.clear_frame("Record table empty\nNothing to display")

    def _delete_selected_records(self):
        """ Called when the 'Delete' button is pressed. Deletes all of the selected records
        (and the associated images) from the store and from disk. Asks for user confirmation.
        """
        # Display a confirmation dialog to check that user wants to proceed with deletion
        quit_msg = "This operation cannot be undone.\nAre you sure you want to delete these record/s?"
        reply = QtWidgets.QMessageBox.warning(self, 'Confirm Delete',
                         quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        # If yes, find the appropriate records and delete them
        if reply == QMessageBox.Yes:
            rows = self._table.selectionModel().selectedRows()
            records_to_delete = []
            for row in rows:
                index = row.row()
                record = self._store.get_record(index)
                records_to_delete.append(record)

            if self._options.backup.value():
                self._store.backup_records(self._options.get_backup_directory())
            self._store.delete_records(records_to_delete)

            self._load_store_records()

    def is_latest_holder_barcode(self, holder_barcode):
        return self._store.is_latest_holder_barcode(holder_barcode)


