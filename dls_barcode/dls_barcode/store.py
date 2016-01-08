import time
import datetime
import uuid
import os

import pyperclip
from PyQt4 import QtGui, QtCore

from plate import BAD_DATA_SYMBOL, EMPTY_SLOT_SYMBOL


# MAJOR:
# TODO: Refresh page on delete or new barcode
# TODO: Auto-select the first record on opening the window

# MINOR:
# todo: allow delete key to be used for deletion
# todo: allow record selection with arrow keys
# todo: Allow option to disable image saving



class Record:
    """ Represents a record of a single scan, including the time, type of
    sample holder plate, list of barcodes scanned, and the path of the image
    of the scan (if any). Can be written to and read from file.
    """

    # Indices for ordering of data when a record is written to or read from a string
    IND_ID = 0
    IND_TIMESTAMP = 1
    IND_IMAGE = 2
    IND_PLATE = 3
    IND_BARCODES = 4
    NUM_RECORD_ITEMS = 5

    # Constants
    ITEM_SEPARATOR = ";"
    BC_SEPARATOR = ","
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, plate_type, barcodes, imagepath, timestamp=0, id=0):
        """
        :param plate_type: the type of the sample holder plate (string)
        :param barcodes: ordered array of strings giving the barcodes in each slot
            of the plate in order. Empty slots should be denoted by empty strings, and invalid
            barcodes by the BAD_DATA_SYMBOL.
        :param imagepath: the absolute path of the image.
        :param timestamp: number of seconds since the epoch (use time.time(); generated
            automatically if a value isn't supplied
        :param id: uid for the record; one will be generated if not supplied
        """
        self.timestamp = float(timestamp)
        self.imagepath = imagepath
        self.plate_type = plate_type
        self.barcodes = barcodes
        self.id = str(id)

        # Generate timestamp and uid if none are supplied
        if timestamp==0:
            self.timestamp = time.time()
        if id==0:
            self.id = str(uuid.uuid4())

        # Separate Data and Time
        dt = self._formatted_date().split(" ")
        self.date = dt[0]
        self.time = dt[1]

        # Counts of numbers slots and barcodes
        self.num_slots = len(barcodes)
        self.num_empty_slots = len([b for b in barcodes if b==EMPTY_SLOT_SYMBOL])
        self.num_invalid_barcodes = len([b for b in barcodes if b==BAD_DATA_SYMBOL])
        self.num_valid_barcodes = self.num_slots - self.num_empty_slots - self.num_invalid_barcodes


    @staticmethod
    def from_string(string):
        """ Creates a scan record object from a semi-colon separated string. This is
        used when reading a stored record back from file.
        """
        items = string.strip().split(Record.ITEM_SEPARATOR)
        id = items[Record.IND_ID]
        timestamp = float(items[Record.IND_TIMESTAMP])
        image = items[Record.IND_IMAGE]
        puck_type = items[Record.IND_PLATE]
        barcodes = items[Record.IND_BARCODES].split(Record.BC_SEPARATOR)

        return Record(plate_type=puck_type, barcodes=barcodes, timestamp=timestamp, imagepath=image, id=id)

    def to_string(self):
        """ Converts a scan record object into a string that can be stored in a file
        and retrieved later.
        """
        items = [0] * Record.NUM_RECORD_ITEMS
        items[Record.IND_ID] = str(self.id)
        items[Record.IND_TIMESTAMP] = str(self.timestamp)
        items[Record.IND_IMAGE] = self.imagepath
        items[Record.IND_PLATE] = self.plate_type
        items[Record.IND_BARCODES] = Record.BC_SEPARATOR.join(self.barcodes)
        return Record.ITEM_SEPARATOR.join(items)

    def _formatted_date(self):
        """ Provides a human-readable form of the datetime stamp
        """
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(Record.DATE_FORMAT)


class Store:
    """ Maintains a list of records of previous barcodes scans. Any changes (additions
    or deletions) are automatically written to the backing file.
    """
    def __init__(self, filepath, records):
        """ Initializes a new instance of Store. Users of the class should use the
        static 'from_file' as the __init__ function does not read from the existing
        file, it only stores the path for later writing.
        :param filepath: absolute path of file to write any updates to.
        :param records: list of Record items
        """
        self._filepath = filepath
        self.records = records
        self._sort_records()

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        return self.records[index]

    def add_record(self, record):
        """ Add a new record to the store and save to the backing file.
        """
        self.records.append(record)
        self._process_change()

    def delete_records(self, records):
        """ Remove all of the records in the supplied list from the store and
        save changes to the backing file.
        """
        for record in records:
            self.records.remove(record)
            if os.path.isfile(record.imagepath):
                os.remove(record.imagepath)
        self._process_change()

    def _process_change(self):
        """ Sort the records and save to file.
        """
        self._sort_records()
        self._to_file()

    def _sort_records(self):
        """ Sort the records in descending date order (must recent first).
        """
        self.records.sort(reverse=True, key=lambda record: record.timestamp)

    def _to_file(self):
        """ Save the contents of the store to the backing file
        """
        record_lines = [rec.to_string() for rec in self.records]
        file_contents = "\n".join(record_lines)
        with open(self._filepath, mode="wt") as file:
            file.writelines(file_contents)

    @staticmethod
    def from_file(filepath):
        """ Create a store object by reading a set of
        records from a file
        """
        records = []
        if not os.path.isfile(filepath):
            return Store(filepath, records)

        with open(filepath, mode="rt") as file:
            lines = [line for line in file]

            for line in lines:
                try:
                    record = Record.from_string(line)
                    records.append(record)
                except Exception:
                    pass
        return Store(filepath, records)




class StoreDialog(QtGui.QDialog):
    """ A Qt window that displays the contents of a store, i.e., a list of previous barcode
    scans. The list of scans is presented in a table and clicking on a scan record (a row)
    displays the list of barcodes in that scan in a second table, as well as the highlighted
    image of that scan (if available).
    """

    COLOR_RED = QtGui.QColor(255, 0, 0, 100)
    COLOR_GREEN = QtGui.QColor(0, 255, 0, 100)
    COLOR_BLUE = QtGui.QColor(0, 0, 255, 100)
    COLOR_GRAY = QtGui.QColor(128, 128, 128, 100)

    COLUMNS = ['Date', 'Time', 'Plate Type', 'Valid', 'Invalid', 'Empty']

    def __init__(self, store):
        super(StoreDialog, self).__init__()
        self._store = store

        # UI elements
        self._recordTable = None
        self._barcodeTable = None
        self.imageFrame = None

        self._initUI()

    def _initUI(self):
        # Create record table - lists all the records in the store
        self._recordTable = QtGui.QTableWidget(self)
        self._recordTable.setFixedWidth(420)
        self._recordTable.setFixedHeight(600)
        self._recordTable.setColumnCount(len(StoreDialog.COLUMNS))
        self._recordTable.setHorizontalHeaderLabels(StoreDialog.COLUMNS)
        self._recordTable.setColumnWidth(0, 70)
        self._recordTable.setColumnWidth(1, 55)
        self._recordTable.setColumnWidth(2, 85)
        self._recordTable.setColumnWidth(3, 60)
        self._recordTable.setColumnWidth(4, 60)
        self._recordTable.setColumnWidth(5, 60)
        self._recordTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self._recordTable.setRowCount(len(self._store.records))
        self._fill_record_table(self._store)
        self._recordTable.cellPressed.connect(self._new_row_selected)

        # Create barcode table - lists all the barcode sin a record
        self._barcodeTable = QtGui.QTableWidget()
        self._barcodeTable.setFixedWidth(110)
        self._barcodeTable.setFixedHeight(600)
        self._barcodeTable.setColumnCount(1)
        self._barcodeTable.setRowCount(10)
        self._barcodeTable.setHorizontalHeaderLabels(['Barcode'])
        self._barcodeTable.setColumnWidth(0, 100)
        self._barcodeTable.clearContents()

        # Image frame - displays image of the currently selected scan record
        self.imageFrame = QtGui.QLabel()
        self.imageFrame.setStyleSheet("background-color: black; color: red; font-size: 30pt; text-align: center")
        self.imageFrame.setFixedWidth(600)
        self.imageFrame.setFixedHeight(600)

        # Delete button - deletes selected records
        deleteBtn = QtGui.QPushButton('Delete')
        deleteBtn.setToolTip('Delete selected scan/s')
        deleteBtn.resize(deleteBtn.sizeHint())
        deleteBtn.clicked.connect(self._delete_selected_records)

        # Clipboard button - copy the selected barcodes to the clipboard
        clipboardBtn = QtGui.QPushButton('Copy To Clipboard')
        clipboardBtn.setToolTip('Copy barcodes for the selected record to the clipboard')
        clipboardBtn.resize(clipboardBtn.sizeHint())
        clipboardBtn.clicked.connect(self._copy_selected_record_to_clipboard)

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self._recordTable)
        hbox.addWidget(self._barcodeTable)
        hbox.addWidget(self.imageFrame)
        hbox.addStretch(1)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.setSpacing(10)
        hbox2.addWidget(clipboardBtn)
        hbox2.addWidget(deleteBtn)
        hbox2.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        vbox.addStretch(1)
        self.setLayout(vbox)

        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle('Previously Scanned Items')
        self.show()

    def _fill_record_table(self, store):
        """ Populate the record table with all of the records in the store.
        """
        for n, record in enumerate(store.records):
            items = [record.date, record.time, record.plate_type, record.num_valid_barcodes,
                     record.num_invalid_barcodes, record.num_empty_slots]

            if record.num_valid_barcodes == record.num_slots:
                color = StoreDialog.COLOR_GREEN
            elif record.num_invalid_barcodes > 0:
                color = StoreDialog.COLOR_RED
            else:
                color = StoreDialog.COLOR_BLUE

            for m, item in enumerate(items):
                newitem = QtGui.QTableWidgetItem(str(item))
                newitem.setBackgroundColor(color)
                newitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self._recordTable.setItem(n, m, newitem)

    def _new_row_selected(self):
        """ Called when a row is selected, causes details of the selected record to be
        displayed (list of barcodes oin the barcode table and image of the scan in the
        image frame).
        """
        try:
            row = self._recordTable.selectionModel().selectedRows()[0].row()
            record = self._store.get_record(row)
            self._fill_barcode_table(record.barcodes)
            self._display_image(record.imagepath)
        except IndexError:
            self._fill_barcode_table([])
            self._display_image(None)

    def _fill_barcode_table(self, barcodes):
        """ Called when a new row is selected on the record table. Displays all of the
        barcodes from the selected record in the barcode table. Valid barcodes are
        highlighted green, invalid barcodes are highlighted red, and empty slots are grey.
        """
        num_slots = len(barcodes)
        self._barcodeTable.clearContents()
        self._barcodeTable.setRowCount(num_slots)

        for index, barcode in enumerate(barcodes):
            # Select appropriate background color
            if barcode == BAD_DATA_SYMBOL:
                color = StoreDialog.COLOR_RED
            elif barcode == EMPTY_SLOT_SYMBOL:
                color = StoreDialog.COLOR_GRAY
            else:
                color = StoreDialog.COLOR_GREEN

            # Set table item
            barcode = QtGui.QTableWidgetItem(barcode)
            barcode.setBackgroundColor(color)
            barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self._barcodeTable.setItem(index, 0, barcode)

    def _display_image(self, filename):
        """ Called when a new row is selected on the record table. Displays the specified
        image (image of the highlighted scan) in the image frame
        """
        self.imageFrame.clear()
        self.imageFrame.setAlignment(QtCore.Qt.AlignCenter)

        if filename is None:
            self.imageFrame.setText("No Scan Selected")
        elif os.path.isfile(filename):
            pixmap = QtGui.QPixmap(filename)
            self.imageFrame.setPixmap(pixmap.scaled(self.imageFrame.size(),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        else:
            self.imageFrame.setText("Image Not Found")


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
            rows = self._recordTable.selectionModel().selectedRows()
            records_to_delete = []
            for row in rows:
                index = row.row()
                record = self._store.get_record(index)
                records_to_delete.append(record)

            self._store.delete_records(records_to_delete)

    def _copy_selected_record_to_clipboard(self):
        """ Called when the copy to clipboard button is pressed. Copies the list/s of
        barcodes for the currently selected records to the clipboard so that the user
        can paste it elsewhere.
        """
        rows = self._recordTable.selectionModel().selectedRows()
        rows = sorted([row.row() for row in rows])
        barcodes = []
        for row in rows:
            record = self._store.get_record(row)
            barcodes.extend(record.barcodes)

        if barcodes:
            pyperclip.copy('\n'.join(barcodes))
        #spam = pyperclip.paste()






