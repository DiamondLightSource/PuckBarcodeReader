import time
import datetime
import uuid
import os
from PyQt4 import QtGui, QtCore

ITEM_SEPARATOR = ";"
BC_SEPARATOR = ","
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BAD_DATA_SYMBOL = "XXXXXXX"

IND_ID = 0
IND_TIMESTAMP = 1
IND_IMAGE = 2
IND_PUCK = 3
IND_BARCODES = 4
NUM_RECORD_ITEMS = 5

# TODO: This doesn't currently handle the case where a new barcode is scanned while the window is open


class Record:
    """ Represent a record of a single scan, including the time, type of
    sample holder plate, list of barcodes scanned, and the path of the image
    of the scan (if any).
    """
    def __init__(self, puck_type, barcodes, imagepath, timestamp=0, id=0):
        self.timestamp = float(timestamp)
        self.imagepath = imagepath
        self.puck_type = puck_type
        self.barcodes = barcodes
        self.id = str(id)

        if timestamp==0:
            self.timestamp = time.time()

        if id==0:
            self.id = str(uuid.uuid4())

        dt = self.formatted_date().split(" ")
        self.date = dt[0]
        self.time = dt[1]

        self.num_valid_barcodes = len([b for b in barcodes if (b!='' and b!=BAD_DATA_SYMBOL)])

    @staticmethod
    def from_string(string):
        """ Creates a scan record object from a string
        """
        items = string.strip().split(ITEM_SEPARATOR)
        id = items[IND_ID]
        timestamp = float(items[IND_TIMESTAMP])
        image = items[IND_IMAGE]
        puck_type = items[IND_PUCK]
        barcodes = items[IND_BARCODES].split(BC_SEPARATOR)

        return Record(puck_type=puck_type, barcodes=barcodes, timestamp=timestamp, imagepath=image, id=id)

    def to_string(self):
        """ Converts a scan record object into a string that can be stored in a file
        """
        barcode_str = BC_SEPARATOR.join(self.barcodes)
        items = [0] * NUM_RECORD_ITEMS
        items[IND_ID] = str(self.id)
        items[IND_TIMESTAMP] = str(self.timestamp)
        items[IND_IMAGE] = self.imagepath
        items[IND_PUCK] = self.puck_type
        items[IND_BARCODES] = BC_SEPARATOR.join(self.barcodes)
        return ITEM_SEPARATOR.join(items)

    def formatted_date(self):
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(DATE_FORMAT)


class Store:
    def __init__(self, filepath, records):
        self.filepath = filepath

        self.records = records
        self._sort_records()

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        return self.records[-index - 1]

    def add_record(self, record):
        self.records.append(record)
        self._process_change()

    def delete_records(self, records):
        for record in records:
            self.records.remove(record)
            if os.path.isfile(record.imagepath):
                os.remove(record.imagepath)

        self._process_change()

    def _process_change(self):
        self._sort_records()
        self.to_file()

    def to_file(self):
        record_lines = [rec.to_string() for rec in self.records]
        file_contents = "\n".join(record_lines)
        with open(self.filepath, mode="wt") as file:
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

    def _sort_records(self):
        self.records.sort(key=lambda record: record.timestamp)



class StoreDialog(QtGui.QDialog):
    def __init__(self, store):
        super(StoreDialog, self).__init__()
        self.store = store

        self.recordTable = None
        self.barcodeTable = None
        self.imageFrame = None

        self.initUI()

    def initUI(self):
        # Create record table
        self.recordTable = QtGui.QTableWidget(self)
        self.recordTable.setFixedWidth(300)
        self.recordTable.setFixedHeight(600)
        self.recordTable.setColumnCount(4)
        self.recordTable.setHorizontalHeaderLabels(['Date','Time','PuckType','Barcodes'])
        self.recordTable.setColumnWidth(0, 70)
        self.recordTable.setColumnWidth(1, 55)
        self.recordTable.setColumnWidth(2, 85)
        self.recordTable.setColumnWidth(3, 60)
        self.recordTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.recordTable.setRowCount(len(self.store.records))
        self.fill_record_table(self.store)
        self.recordTable.cellClicked.connect(self.new_row_selected)

        # Create barcode table
        self.barcodeTable = QtGui.QTableWidget()
        self.barcodeTable.setFixedWidth(110)
        self.barcodeTable.setFixedHeight(600)
        self.barcodeTable.setColumnCount(1)
        self.barcodeTable.setRowCount(10)
        self.barcodeTable.setHorizontalHeaderLabels(['Barcode'])
        self.barcodeTable.setColumnWidth(0, 100)
        self.barcodeTable.clearContents()

        # Image frame
        self.imageFrame = QtGui.QLabel()
        self.imageFrame.setStyleSheet("background-color: black; color: red; font-size: 30pt; text-align: center")
        self.imageFrame.setFixedWidth(600)
        self.imageFrame.setFixedHeight(600)

        # Delete button
        delBtn = QtGui.QPushButton('Delete')
        delBtn.setToolTip('Delete selected scan/s')
        delBtn.resize(delBtn.sizeHint())
        delBtn.clicked.connect(self.delete_selected_records)

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.recordTable)
        hbox.addWidget(self.barcodeTable)
        hbox.addWidget(self.imageFrame)
        hbox.addStretch(1)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.setSpacing(10)
        hbox2.addWidget(delBtn)
        hbox2.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        vbox.addStretch(1)
        self.setLayout(vbox)

        self.setGeometry(100, 100, 900, 700)
        self.setWindowTitle('Previously Scanned Items')
        self.show()

    def fill_record_table(self, store):
        for n, record in enumerate(reversed(store.records)):
            items = [record.date, record.time, record.puck_type, record.num_valid_barcodes]
            for m, item in enumerate(items):
                newitem = QtGui.QTableWidgetItem(str(item))
                newitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.recordTable.setItem(n, m, newitem)

    def new_row_selected(self):
        row = self.recordTable.selectionModel().selectedRows()[0].row()
        try:
            record = self.store.get_record(row)
            self.fill_barcode_table(record.barcodes)
            self.display_image(record.imagepath)
        except IndexError:
            self.fill_barcode_table([])

    def fill_barcode_table(self, barcodes):
        num_slots = len(barcodes)
        self.barcodeTable.clearContents()
        self.barcodeTable.setRowCount(num_slots)
        for index, barcode in enumerate(barcodes):
            # Barcode data column
            if barcode == BAD_DATA_SYMBOL:
                barcode = QtGui.QTableWidgetItem(barcode)
                barcode.setBackgroundColor(QtGui.QColor(255, 0, 0, 100))
                barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.barcodeTable.setItem(index, 0, barcode)
            elif barcode != '':
                barcode = QtGui.QTableWidgetItem(barcode)
                barcode.setBackgroundColor(QtGui.QColor(0, 255, 0, 100))
                barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.barcodeTable.setItem(index, 0, barcode)
            else:
                barcode = QtGui.QTableWidgetItem()
                barcode.setBackgroundColor(QtGui.QColor(128, 128, 128, 100))
                barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.barcodeTable.setItem(index, 0, barcode)

    def display_image(self, filename):
        if os.path.isfile(filename):
            pixmap = QtGui.QPixmap(filename)
            self.imageFrame.setPixmap(pixmap.scaled(self.imageFrame.size(),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            self.imageFrame.setAlignment(QtCore.Qt.AlignCenter)
        else:
            self.imageFrame.clear()
            self.imageFrame.setText("Image Not Found")
            self.imageFrame.setAlignment(QtCore.Qt.AlignCenter)

    def delete_selected_records(self):
        quit_msg = "This operation cannot be undone.\nAre you sure you want to delete these record/s?"
        reply = QtGui.QMessageBox.warning(self, 'Confirm Delete',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        # TODO: refresh the page after deletes

        if reply == QtGui.QMessageBox.Yes:
            rows = self.recordTable.selectionModel().selectedRows()
            records_to_delete = []
            for row in rows:
                index = row.row()
                record = self.store.get_record(index)
                records_to_delete.append(record)

            self.store.delete_records(records_to_delete)






