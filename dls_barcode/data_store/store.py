import uuid
import os
import time

from dls_barcode.data_store.backup import Backup
from dls_barcode.data_store.comms_manager import CommsManager
from .record import Record


class Store:

    """ Maintains a list of records of previous barcodes scans. Any changes (additions
    or deletions) are automatically written to the backing file.
    """

    def __init__(self, comms_manager):
        """ Initializes a new instance of Store.
        """
        self._comms_manager = comms_manager
        self._comms_manager.make_img_dir()
        self._img_dir = self._comms_manager.get_img_dir()
        records = self._comms_manager.load_records_from_file()
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

    def backup_records(self, directory):
        ts = time.localtime()
        file_name = time.strftime("%Y-%m-%d_%H-%M-%S", ts)
        backup_manger = CommsManager(directory, file_name)
        backup = Backup(backup_manger)
        backup.backup_records(self.records)

    def delete_records(self, records_to_delete):
        """ Remove all of the records in the supplied list from the store and
        save changes to the backing file.
        """
        for record in records_to_delete:
            self.records.remove(record)
            self._comms_manager.remove_img_file(record)

        self._process_change()


    def _process_change(self):
        """ Sort the records and save to file.
        """
        self._sort_records()
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
