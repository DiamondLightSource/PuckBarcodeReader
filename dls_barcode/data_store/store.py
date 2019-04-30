import uuid
import time

from dls_barcode.data_store.backup import Backup
from dls_barcode.data_store.store_writer import StoreWriter
from .record import Record


class Store:

    """ Maintains a list of records of previous barcodes scans. Any changes (additions
    or deletions) are automatically written to the backing file.
    """

    def __init__(self, store_writer, records):
        """ Initializes a new instance of Store.
        """
        self._store_writer = store_writer
        self.records = records

    def size(self):
        """ Returns the number of records in the store
        """
        return len(self.records)

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        self._sort_records()
        return self.records[index] if self.records else None

    def _add_record(self, holder_barcode, plate, holder_img, pins_img):
        """ Add a new record to the store and save to the backing file.
        """
        merged_img = self._merge_holder_image_into_pins_image(holder_img, pins_img)
        guid = str(uuid.uuid4())
        self._store_writer.to_image(merged_img, guid)

        record = Record.from_plate(holder_barcode, plate, self._store_writer.get_img_path())

        self.records.append(record)
        self._process_change()

    def merge_record(self, holder_barcode, plate, holder_img, pins_img):
        """ Create new record or replace existing record if it has the same holder barcode as the most
        recent record. Save to backing store. """
        if self.records and self.records[0].holder_barcode == holder_barcode:
            self.delete_records([self.records[0]])

        self._add_record(holder_barcode, plate, holder_img, pins_img)

    def backup_records(self, directory):
        ts = time.localtime()
        file_name = time.strftime("%Y-%m-%d_%H-%M-%S", ts)
        backup_writer = StoreWriter(directory, file_name)
        backup = Backup(backup_writer)
        self._sort_records()
        backup.backup_records(self.records)

    def delete_records(self, records_to_delete):
        """ Remove all of the records in the supplied list from the store and
        save changes to the backing file.
        """
        for record in records_to_delete:
            self.records.remove(record)
            self._store_writer.remove_img_file(record)

        self._process_change()

    def _process_change(self):
        """ Sort the records and save to file.
        """
        self._sort_records()
        self._store_writer.to_file(self.records)
        self._store_writer.to_csv_file(self.records)

    def _sort_records(self):
        """ Sort the records in descending date order (most recent first).
        """
        self.records.sort(reverse=True, key=lambda record: record.timestamp)

    def _merge_holder_image_into_pins_image(self, holder_img, pins_img):
        factor = 0.22 * pins_img.width / holder_img.width
        small_holder_img = holder_img.rescale(factor)

        merged_img = pins_img.copy()
        merged_img.paste(small_holder_img, 0, 0)
        return merged_img

    def is_latest_holder_barcode(self, holder_barcode):
        self._sort_records()
        latest_record = self.get_record(0)
        return latest_record is not None and holder_barcode == latest_record.holder_barcode
