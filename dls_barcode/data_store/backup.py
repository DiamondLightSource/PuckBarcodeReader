import time

from dls_barcode.data_store.comms_manager import CommsManager


class Backup:

    """
    Backup class maintains the short time backaup of records which is kept in the same folder as the store files.
    """

    def __init__(self, comms_man, backup_time):
        self._comms = comms_man
        self._backup_time = backup_time.value()
        self._records = self._comms.load_records_from_file()
        self._truncate_record_list()

    def _truncate_record_list(self):
        for record in self._records:
            if self._is_old(record):
                self._records.remove(record)

    def backup_records(self, to_back):
        self._records.extend(to_back)
        self._truncate_record_list()
        self._comms.to_csv_file(self._records)

    def _is_old(self, record):
        tm = time.time()
        record_time = record.timestamp
        delta = tm - record_time
        weeks = self._backup_time * 604800  # weeks in seconds
        return delta > weeks

