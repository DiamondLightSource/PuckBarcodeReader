from __future__ import division

from datetime import datetime
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget, QMessageBox

from dls_barcode.data_store import Store
from dls_barcode.data_store.store_loader import StoreLoader
from dls_barcode.data_store.store_writer import StoreWriter
from dls_barcode.data_store.session_manager import SessionManager

# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys

RED = "; color: red"
BLACK = "; color: black"
BASIC_STYLE_SHEET = "font-size: 12pt"

class ScanRecordTable(QGroupBox):
    """ GUI component. Displays a list of previous scan results. Selecting a scan causes
    details of the scan to appear in other GUI components (list of barcodes in the barcode
    table and image of the puck in the image frame).
    """
    COLUMNS = ['Date', 'Time', 'Plate Barcode', 'Valid', 'Invalid', 'Empty', 'Plate Type']

    def __init__(self, barcode_table, image_frame, options):
        super(ScanRecordTable, self).__init__()

        # Read the store from file
        store_writer = StoreWriter(options.get_store_directory(), "store")
        store_loader = StoreLoader(options.get_store_directory(), "store")

        self._store = Store(store_writer, store_loader.load_records_from_file())
        self._options = options

        # Create the session  manager and a file writer for sessions
        session_writer = StoreWriter(options.get_session_directory(), "session")
        self._session_manager = SessionManager(session_writer, self._store)
        self._session_manager.new_session()

        self._barcodeTable = barcode_table
        self._imageFrame = image_frame

        self.setTitle("Scan Records")
        self.setMaximumWidth(730)

        self._init_ui()

        self._load_store_records()

    def _init_ui(self):
        # Create record table - lists all the records in the store
        self._table = QTableWidget()
        self._table.setMinimumWidth(720) #900
        self._table.setMinimumHeight(600)
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)

        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        #Session
        self._current_session_id_label = QtWidgets.QLabel()
        self._current_session_id_label.setStyleSheet(BASIC_STYLE_SHEET + RED)
        self._new_session_button = QtWidgets.QPushButton("New Session")
        self._new_session_button.setStatusTip("Create a new session")
        self._new_session_button.clicked.connect(self._new_session_clicked)
        self._end_session_button = QtWidgets.QPushButton("End Session")
        self._end_session_button.setStatusTip("End the current session")
        self._end_session_button.clicked.connect(self._end_session_clicked)
        self._save_session_button = QtWidgets.QPushButton("Save Session")
        self._save_session_button.setStatusTip("Save the current session")
        self._save_session_button.clicked.connect(self._save_session_clicked)

        self._new_session_button.setMaximumWidth(100)
        self._end_session_button.setMaximumWidth(100)
        self._save_session_button.setMaximumWidth(100)

        vbox = QVBoxLayout()

        hbox = QHBoxLayout()
        hbox.setSpacing(0)
        hbox.addWidget(self._new_session_button)
        hbox.addWidget(self._save_session_button)
        hbox.addWidget(self._end_session_button)
        hbox.addStretch(1)
        hbox.addWidget(self._current_session_id_label)
        vbox.addLayout(hbox)

        # Delete button - deletes selected records
        btn_delete = QtWidgets.QPushButton('Delete')
        btn_delete.setToolTip('Delete selected scan/s')
        btn_delete.resize(btn_delete.sizeHint())
        btn_delete.clicked.connect(self._delete_selected_records)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(btn_delete)
        hbox.addStretch(1)

        vbox.addWidget(self._table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self._update_session()

    def cell_pressed_action_triggered(self, to_run_on_table_clicked):
        self._table.cellPressed.connect(to_run_on_table_clicked)
        self._table.cellPressed.connect(self._record_selected)

    def change_session_action_triggered(self, on_change_session_action_clicked):
        self._new_session_button.clicked.connect(on_change_session_action_clicked)
        self._end_session_button.clicked.connect(on_change_session_action_clicked)

    def add_record_frame(self, holder_barcode, plate, holder_img, pins_img):
        """ Add a new scan frame - creates a new record if its a new puck, else merges with previous record"""
        self._store.merge_record(holder_barcode, plate, holder_img, pins_img)
        self._load_store_records()
        if self._options.scan_clipboard.value():
            self._barcodeTable.copy_to_clipboard()

    def _load_store_records(self):
        """ Populate the record table with all of the records in the store.
        """
        start_time = self._session_manager.current_session_id
        self._table.clearContents()
        self._table.setRowCount(self._store.size(start_time))

        for n, record in enumerate(self._store.records):
            if start_time < record.timestamp:
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
            row = self._table.selectionModel().selectedRows()[0].row()
            record = self._store.get_record(row)
            self._barcodeTable.populate(record.holder_barcode, record.barcodes)
            marked_image = record.marked_image(self._options)
            self._imageFrame.display_puck_image(marked_image)
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

    def _update_session(self):
        if self._session_manager.current_session_id:
            self._current_session_id_label.setStyleSheet(BASIC_STYLE_SHEET + BLACK)
            self._current_session_id_label.setText(
                "Session active: {}".format(self._session_manager.current_session_timestamp)
            )
        else:
            self._current_session_id_label.setStyleSheet(BASIC_STYLE_SHEET + RED)
            self._current_session_id_label.setText("No active session, showing all results in store")
        self._imageFrame.clear_frame("")
        self._load_store_records()

    def _new_session_clicked(self):
        """Called when the 'New Session' button is clicked. Starts a new session"""
        # Multiple sessions within a one second period are not allowed as they would
        # have the same session id. Disable the new session button for one second.
        self._new_session_button.setEnabled(False)
        self._save_session_button.setDisabled(False)
        QTimer.singleShot(1000, lambda: self._new_session_button.setDisabled(False))
        self._session_manager.new_session()
        self._update_session()

    def _end_session_clicked(self):
        """Called when the 'End Session' button is clicked. Ends the active session"""
        self._save_session_button.setEnabled(False)
        self._session_manager.end_session()
        self._update_session()

    def _save_session_clicked(self):
        """Called when the 'Save Session' button is clicked.
        Saves csv file with records in current session"""
        were_records_saved = self._session_manager.save_session()
        saved_msg = (
            "Records saved to {}".format(self._session_manager.last_saved_file)
            if were_records_saved else "No records to save")
        reply = QMessageBox.information(self, 'Save Session', saved_msg, QMessageBox.Ok)

    def is_latest_holder_barcode(self, holder_barcode):
        return self._store.is_latest_holder_barcode(holder_barcode, self._session_manager.current_session_id)


