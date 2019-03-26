import time

from dls_barcode.data_store.comms_manager import CommsManager


class Backup:

    """
    Backup class maintains the short time backaup of records which is kept in the same folder as the store files.
    """

    MAX_BACKUP_TIME = 6   # maximum backup time in weeks

    def __init__(self, directory, backup_time):
        self.comms = CommsManager(directory, "backup")
        self.backup_time = backup_time
        self.records = self.comms.load_records_from_file()
        self._truncate_record_list()

    def _truncate_record_list(self):
        for record in self.records:
            if self._is_old(record):
                self.records.remove(record)

    def backup_records(self, to_back):
        self.records.extend(to_back)
        self._truncate_record_list()
        self.comms.to_csv_file(self.records)

    def _is_old(self, record):
        tm = time.time()
        record_time = record.timestamp
        delta = tm - record_time
        backup_time = min(self.backup_time, self.MAX_BACKUP_TIME)
        weeks = backup_time * 604800  # weeks in seconds
        return delta > weeks

