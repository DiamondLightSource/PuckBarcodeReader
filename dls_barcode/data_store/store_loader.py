import os

from dls_barcode.data_store.record import Record
from dls_util.file import FileManager


class StoreLoader:

    def __init__(self, directory, file_name, file_manager=FileManager()):
        self._directory = directory
        self._file_name = file_name
        self._file_manager= file_manager
        self._path = None
        self._records = []

    def load_records_from_file(self):
        """ Clear the current record store and load a new set of records from the specified file. """
        self._build_file_path()
        if not self._check_if_file():
            return self._records
        self._build_records_from_lines(self._read_lines())
        return self._records

    def _build_file_path(self):
        self._path =  os.path.join(self._directory, self._file_name + '.txt')

    def _check_if_file(self):
        return self._file_manager.is_file(self._path)

    def _read_lines(self):
        return self._file_manager.read_lines(self._path)

    def _build_records_from_lines(self, lines):
        for line in lines:
            try:
                record = Record.from_string(line)
                self._records.append(record)
            except Exception:
                print("Failed to parse store Record: {}".format(line))
