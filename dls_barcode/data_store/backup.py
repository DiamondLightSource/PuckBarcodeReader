import time

from dls_barcode.data_store.record import Record
from dls_util.file import FileManager


class Backup:

    def __init__(self, backup_file):
        self._backup_file = backup_file
        self._file_manager = FileManager()
        self._load_records_from_file()

    def _load_records_from_file(self):
        """ Clear the current record store and load a new set of records from the specified file. """
        self.records = []

        if not self._file_manager.is_file(self._backup_file):
            return

        lines = self._file_manager.read_lines(self._backup_file)
        for line in lines:
            try:
                record = Record.from_string(line)
                self.records.append(record)
            except Exception:
                print("Failed to parse store Record: {}".format(line))

        #self._truncate_record_list()

    def _to_backup_file(self):
        """ Save the contents of the store to the backing file
        """
        record_lines = [rec.to_string() + "\n" for rec in self.records]
        self._file_manager.write_lines(self._backup_file, record_lines)

    def _truncate_record_list(self):
        for record in self.records:
            if self._is_old(record):
                self.records.remove(record)

    def backup_records(self, to_back):
        self.records.extend(to_back)
        self._truncate_record_list()
        self._to_backup_file()

    def _is_old(self,record):
        tm = time.time()
        record_time = record.timestamp
        delta = tm - record_time
        weeks = 3 * 604800 #3 weeks in seconds
        return delta > weeks

