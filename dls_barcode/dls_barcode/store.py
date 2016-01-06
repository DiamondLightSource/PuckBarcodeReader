import time
import datetime
from PyQt4 import QtGui, QtCore

ITEM_SEPARATOR = ";"
BC_SEPARATOR = ","
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BAD_DATA_SYMBOL = "XXXXXXX"

# TODO: This doesn't currently handle the case where a new barcode is scanned while the window is open


class Record:
    """ Represent a record of a single scan, including the time, type of
    sample holder plate, list of barcodes scanned, and the path of the image
    of the scan (if any).
    """
    def __init__(self, puck_type, barcodes, imagepath="", timestamp=0):
        self.timestamp = float(timestamp)
        self.imagepath = imagepath
        self.puck_type = puck_type
        self.barcodes = barcodes

        if timestamp==0:
            self.timestamp = time.time()

        dt = self.formatted_date().split(" ")
        self.date = dt[0]
        self.time = dt[1]

    @staticmethod
    def from_string(string):
        """ Creates a scan record object from a string
        """
        items = string.strip().split(ITEM_SEPARATOR)
        timestamp = float(items[0])
        image = items[1]
        puck_type = items[2]
        barcodes = items[3].split(BC_SEPARATOR)

        return Record(puck_type=puck_type, barcodes=barcodes, timestamp=timestamp, imagepath=image)

    def to_string(self):
        """ Converts a scan record object into a string that can be stored in a file
        """
        barcode_str = BC_SEPARATOR.join(self.barcodes)
        items = [str(self.timestamp), self.imagepath, self.puck_type, barcode_str]
        return ITEM_SEPARATOR.join(items)

    def formatted_date(self):
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(DATE_FORMAT)


class Store:
    def __init__(self, filepath, records):
        self.filepath = filepath

        self.Records = records
        self._sort_records()

    def add_record(self, record):
        self.Records.append(record)
        self._sort_records()
        self.to_file()

    def remove_record(self, record):
        self.Records.remove(record)

    def to_file(self):
        record_lines = [rec.to_string() for rec in self.Records]
        file_contents = "\n".join(record_lines)
        with open(self.filepath, mode="wt") as file:
            file.writelines(file_contents)

    @staticmethod
    def from_file(filepath):
        """ Create a store object by reading a set of
        records from a file
        """
        records = []
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
        self.Records.sort(key=lambda record: record.timestamp)



class StoreDialog(QtGui.QDialog):
    def __init__(self, store):
        super(StoreDialog, self).__init__()
        self.store = store

        self.recordTable = None
        self.barcodeTable = None

        self.initUI()

    def initUI(self):
        # Create record table
        self.recordTable = QtGui.QTableWidget(self)
        self.recordTable.setFixedWidth(700)
        self.recordTable.setFixedHeight(600)
        self.recordTable.setColumnCount(5)
        self.recordTable.setHorizontalHeaderLabels(['Date','Time','PuckType','Image','barcodes'])
        self.recordTable.setColumnWidth(0, 70)
        self.recordTable.setColumnWidth(1, 60)
        self.recordTable.setColumnWidth(2, 100)
        self.recordTable.setColumnWidth(3, 100)
        self.recordTable.setColumnWidth(4, 300)
        self.recordTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.recordTable.setRowCount(len(self.store.Records))
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

        # Create layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.recordTable)
        hbox.addWidget(self.barcodeTable)
        hbox.addStretch(1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addStretch(1)
        self.setLayout(vbox)

        self.setGeometry(100, 100, 900, 700)
        self.setWindowTitle('Previously Scanned Items')
        self.show()

    def fill_record_table(self, store):
        for n, record in enumerate(reversed(store.Records)):
            barcodes = ', '.join(record.barcodes)
            items = [record.date, record.time, record.puck_type, record.imagepath, barcodes]
            for m, item in enumerate(items):
                newitem = QtGui.QTableWidgetItem(str(item))
                newitem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.recordTable.setItem(n, m, newitem)

    def new_row_selected(self):
        row = self.recordTable.selectionModel().selectedRows()[0].row()
        print row
        try:
            record = self.store.Records[-row-1]
            self.fill_barcode_table(record.barcodes)
        except IndexError:
            self.fill_barcode_table([])

    def fill_barcode_table(self, barcodes):
        num_slots = len(barcodes)
        self.barcodeTable.clearContents()
        self.barcodeTable.setRowCount(num_slots)
        print barcodes
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



