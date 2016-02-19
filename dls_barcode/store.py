import time
import datetime
import uuid
import os

from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL
from dls_barcode.datamatrix import BAD_DATA_SYMBOL

STORE_IMAGE_PATH = '../test-output/img_store/'


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
        self.num_empty_slots = len([b for b in barcodes if b == EMPTY_SLOT_SYMBOL])
        self.num_unread_slots = len([b for b in barcodes if b == NOT_FOUND_SLOT_SYMBOL])
        self.num_invalid_barcodes = len([b for b in barcodes if b==BAD_DATA_SYMBOL])
        self.num_valid_barcodes = self.num_slots - self.num_unread_slots \
                                  - self.num_invalid_barcodes - self.num_empty_slots


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
        return Record.ITEM_SEPARATOR.join(items)

    def any_barcode_matches(self, plate):
        """ Returns true if the record contains any barcode which is also
        contained by the specified plate
        """
        barcodes = [bc for bc in plate.barcodes() if bc != '' and bc != BAD_DATA_SYMBOL]
        for bc in barcodes:
            if bc in self.barcodes:
                return True

        return False

    def _formatted_date(self):
        """ Provides a human-readable form of the datetime stamp
        """
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(Record.DATE_FORMAT)


class Store():
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

    def size(self):
        """ Returns the number of records in the store
        """
        return len(self.records)

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        return self.records[index] if self.records else None

    def add_record(self, plate_type, barcodes, cv_img):
        """ Add a new record to the store and save to the backing file.
        """
        id = str(uuid.uuid4())
        filename = os.path.abspath(STORE_IMAGE_PATH + id + '.png')
        cv_img.save_as(filename)

        record = Record(plate_type=plate_type, barcodes=barcodes, imagepath=filename, timestamp=0, id=id)

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
