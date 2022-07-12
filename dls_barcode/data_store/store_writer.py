import os

from dls_barcode.data_store.record import Record
from dls_util.file import FileManager


class StoreWriter:
    """ Maintains writing records to file and saving png images in a sub-folder
    """

    def __init__(self, directory, file_name, file_manager=FileManager()):
        self._file_manager = file_manager
        self._directory = directory
        self._file_name = file_name
        self._image_path = None
        self._holder_image_path = None

    def to_file(self, records):
        """ Save the contents of the store to the backing file
        """
        self._file_manager.make_dir_when_no_dir(self._directory)
        file = os.path.join(self._directory, self._file_name + '.txt')
        record_lines = [rec.to_string() + "\n" for rec in records]
        self._file_manager.write_lines(file, record_lines)

    def to_csv_file(self, records):
        """ Save the contents of the store to the backing csv file
        """
        self._file_manager.make_dir_when_no_dir(self._directory)
        csv_file = os.path.join(self._directory, self._file_name + ".csv")
        record_lines = [rec.to_csv_string() + "\n" for rec in records]
        self._file_manager.write_lines(csv_file, record_lines)

    def to_image(self, pin_image, holder_image, name):
        dr = self._make_img_dir()
        self._image_path = os.path.abspath(os.path.join(dr, name + '.png'))
        self._holder_image_path = os.path.abspath(os.path.join(dr, name + '_holder.png'))
        pin_image.save_as(self._image_path)
        holder_image.save_as(self._holder_image_path)

    def get_img_path(self):
        return self._image_path
    
    def get_holder_img_path(self):
        return self._holder_image_path

    def _make_img_dir(self):
        self._file_manager.make_dir_when_no_dir(self._directory)
        img_dir = os.path.join(self._directory, "img_dir")
        self._file_manager.make_dir_when_no_dir(img_dir)
        return img_dir

    def remove_img_file(self, record):
        if self._file_manager.is_file(record.image_path):
            self._file_manager.remove(record.image_path)
        if self._file_manager.is_file(record.holder_image_path):
            self._file_manager.remove(record.holder_image_path)