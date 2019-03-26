import uuid
import os

from dls_barcode.data_store.backup import Backup
from dls_barcode.data_store.comms_manager import CommsManager
from .record import Record


class Store:

    """ Maintains a list of records of previous barcodes scans. Any changes (additions
    or deletions) are automatically written to the backing file.
    """
    MIN_STORE_CAPACITY = 2

    def __init__(self, directory, store_capacity, backup_time):
        """ Initializes a new instance of Store.
        """
        self._store_capacity = store_capacity
        self._backup = Backup(directory, backup_time)
        self._comms_manager = CommsManager(directory, "store")
        self._img_dir = os.path.join(directory, "img_dir")
        self._comms_manager.make_img_dir(self._img_dir)

        self.records = self._comms_manager.load_records_from_file()
        self._truncate_record_list()
        self._sort_records()

    def size(self):
        """ Returns the number of records in the store
        """
        return len(self.records)

    def get_record(self, index):
        """ Get record by index where the 0th record is the most recent
        """
        return self.records[index] if self.records else None

    def _add_record(self, holder_barcode, plate, holder_img, pins_img):
        """ Add a new record to the store and save to the backing file.
        """
        merged_img = self._merge_holder_image_into_pins_image(holder_img, pins_img)
        guid = str(uuid.uuid4())
        filename = os.path.abspath(os.path.join(self._img_dir, guid + '.png'))
        merged_img.save_as(filename)

        record = Record.from_plate(holder_barcode, plate, filename)

        self.records.append(record)
        self._process_change()

    def merge_record(self, holder_barcode, plate, holder_img, pins_img):
        """ Create new record or replace existing record if it has the same holder barcode as the most
        recent record. Save to backing store. """
        if self.records and self.records[0].holder_barcode == holder_barcode:
            self.delete_records([self.records[0]])

        self._add_record(holder_barcode, plate, holder_img, pins_img)

    def delete_records(self, records_to_delete):
        """ Remove all of the records in the supplied list from the store and
        save changes to the backing file.
        """
        for record in records_to_delete:
            self.records.remove(record)
            self._comms_manager.remove_img_file(record)

        self._process_change()

    def backup_records(self, records_to_backup):
        self._backup.backup_records(records_to_backup)

    def _truncate_record_list(self):

        actual_store_capacity = max(self._store_capacity.value(), self.MIN_STORE_CAPACITY)

        if len(self.records) > actual_store_capacity:
            to_delete = self.records[actual_store_capacity:]
            self.backup_records(to_delete)
            self.delete_records(to_delete)

    def _process_change(self):
        """ Sort the records and save to file.
        """
        self._sort_records()
        self._truncate_record_list()
        self._comms_manager.to_file(self.records)
        self._comms_manager.to_csv_file(self.records)

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
        latest_record = self.get_record(0)
        return latest_record is not None and holder_barcode == latest_record.holder_barcode
