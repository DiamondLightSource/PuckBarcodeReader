import uuid
import os

from .record import Record


class Store:
    """ Maintains a list of records of previous barcodes scans. Any changes (additions
    or deletions) are automatically written to the backing file.
    """
    def __init__(self, directory, options):
        """ Initializes a new instance of Store. Users of the class should use the
        static 'from_file' as the __init__ function does not read from the existing
        file, it only stores the path for later writing.
        """
        self._options = options
        self._directory = directory
        self._file = directory + "store.txt"
        self._csv_file = directory + "store.csv"
        self._img_dir = directory + "/img_dir/"

        if not os.path.exists(self._img_dir):
            os.makedirs(self._img_dir)

        self.records = []
        self._load_records_from_file()
        self._sort_records()

    def _load_records_from_file(self):
        """ Clear the current record store and load a new set of records from the specified file. """
        self.records = []

        if not os.path.isfile(self._file):
            return

        with open(self._file, mode="rt") as file:
            lines = [line for line in file]

            for line in lines:
                try:
                    record = Record.from_string(line)
                    self.records.append(record)
                except Exception:
                    print("Failed to parse store Record: {}".format(line))

        self._truncate_record_list()

    def size(self):
        """ Returns the number of records in the store
        """
        return len(self.records)

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        return self.records[index] if self.records else None

    def add_record(self, plate, second_plate, cv_img):
        """ Add a new record to the store and save to the backing file.
        """
        guid = str(uuid.uuid4())
        filename = os.path.abspath(self._img_dir + guid + '.png')
        cv_img.save_as(filename)

        record = Record.from_plate(plate, second_plate, filename)

        self.records.append(record)
        self._process_change()
        self._truncate_record_list()

    def merge_record(self, plate, second_plate, cv_img):
        """ Create new record or replace existing record if it has the same barcodes as the most
        recent record. Save to backing store. """
        #Checking only side barcodes is sufficient
        #if len(self.records) > 0 and (self.records[0].any_barcode_matches(second_plate.barcodes()) or self.records[0].any_barcode_matches(plate.barcodes())):
        if len(self.records) > 0 and self.records[0].any_barcode_matches(plate.barcodes()):
            self.delete_records([self.records[0]])
            self.add_record(plate, second_plate, cv_img)
        else:
            self.add_record(plate, second_plate, cv_img)

    def delete_records(self, records):
        """ Remove all of the records in the supplied list from the store and
        save changes to the backing file.
        """
        for record in records:
            self.records.remove(record)
            if os.path.isfile(record.image_path):
                os.remove(record.image_path)
        self._process_change()

    def _truncate_record_list(self):
        number = self._options.store_capacity.value()
        number = max(number, 2)

        if len(self.records) > number:
            to_delete = self.records[number:]
            self.delete_records(to_delete)

    def _process_change(self):
        """ Sort the records and save to file.
        """
        self._sort_records()
        self._to_file()
        self._to_csv_file()

    def _sort_records(self):
        """ Sort the records in descending date order (must recent first).
        """
        self.records.sort(reverse=True, key=lambda record: record.timestamp)

    def _to_file(self):
        """ Save the contents of the store to the backing file
        """
        record_lines = [rec.to_string() for rec in self.records]
        file_contents = "\n".join(record_lines)
        with open(self._file, mode="wt") as file:
            file.writelines(file_contents)


    def _to_csv_file(self):
            """ Save the contents of the store to the backing csv file
            """
            record_lines = [rec.to_csv_string() for rec in self.records]
            file_contents = "\n".join(record_lines)
            with open(self._csv_file, mode="wt") as file:
                file.writelines(file_contents)


