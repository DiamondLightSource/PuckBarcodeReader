import os

from dls_barcode.data_store.record import Record
from dls_util.file import FileManager


class CommsManager:
    """ Maintains communication between store/backup and the file manager.
    """

    def __init__(self, directory, file_name):
        self._file_manager = FileManager()
        self._make_dir(directory)
        self._directory = directory
        self._file_name = file_name
        self._img_dir = None

    def load_records_from_file(self):
        """ Clear the current record store and load a new set of records from the specified file. """
        file = os.path.join(self._directory, self._file_name + '.txt')
        records = []

        if not self._file_manager.is_file(file):
            return records

        lines = self._file_manager.read_lines(file)
        for line in lines:
            try:
                record = Record.from_string(line)
                records.append(record)
            except Exception:
                print("Failed to parse store Record: {}".format(line))

        return records

    def to_file(self, records):
        """ Save the contents of the store to the backing file
        """
        file = os.path.join(self._directory, self._file_name + '.txt')
        record_lines = [rec.to_string() + "\n" for rec in records]
        self._file_manager.write_lines(file, record_lines)

    def to_csv_file(self, records):
        """ Save the contents of the store to the backing csv file
        """
        csv_file = os.path.join(self._directory, self._file_name + ".csv")
        record_lines = [rec.to_csv_string() + "\n" for rec in records]
        self._file_manager.write_lines(csv_file, record_lines)

    def make_img_dir(self):
        self._img_dir = os.path.join(self._directory, "img_dir")
        self._make_dir(self._img_dir)

    def get_img_dir(self):
        return self._img_dir

    def _make_dir(self, dr):
        if not self._file_manager.is_dir(dr):
            self._file_manager.make_dir(dr)

    def remove_img_file(self, record):
        if self._file_manager.is_file(record.image_path):
            self._file_manager.remove(record.image_path)