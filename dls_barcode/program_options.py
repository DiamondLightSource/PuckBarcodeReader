import os

from dls_barcode.util.image import Image

TAG_STORE_DIRECTORY = "store_dir"
TAG_SLOT_IMAGES = "slot_images"
TAG_SLOT_IMAGE_DIRECTORY = "slot_img_dir"
TAG_CAMERA_NUMBER = "camera_number"
TAG_CAMERA_WIDTH = "camera_width"
TAG_CAMERA_HEIGHT = "camera_height"

DELIMITER = "="


DEFAULT_STORE_DIRECTORY = "../store/"
DEFAULT_SLOT_IMAGES = False
DEFAULT_SLOT_IMAGE_DIRECTORY = "../debug-output/"
DEFAULT_CAMERA_NUMBER = 0
DEFAULT_CAMERA_WIDTH = 1920
DEFAULT_CAMERA_HEIGHT = 1080


class ProgramOptions:
    def __init__(self, file):
        self._file = file

        self.colour_ok = Image.GREEN
        self.color_not_found = Image.RED
        self.color_unreadable = Image.ORANGE

        self.store_directory = None
        self.slot_images = None
        self.slot_image_directory = None
        self.camera_number = None
        self.camera_width = None
        self.camera_height = None

        self.reset_all()

        self._load_from_file(file)

    def update_config_file(self):
        """ Save the options to the config file. """
        self._save_to_file(self._file)

    def reset_all(self):
        self.store_directory = DEFAULT_STORE_DIRECTORY
        self.slot_images = DEFAULT_SLOT_IMAGES
        self.slot_image_directory = DEFAULT_SLOT_IMAGE_DIRECTORY
        self.camera_number = DEFAULT_CAMERA_NUMBER
        self.camera_width = DEFAULT_CAMERA_WIDTH
        self.camera_height = DEFAULT_CAMERA_HEIGHT

    def _clean_values(self):
        self.store_directory = self.store_directory.strip()
        self.slot_image_directory = self.slot_image_directory.strip()

        if not self.store_directory.endswith("/"):
            self.store_directory += "/"

        if not self.slot_image_directory.endswith("/"):
            self.slot_image_directory += "/"

        try:
            self.camera_number = int(self.camera_number)
        except ValueError:
            self.camera_number = DEFAULT_CAMERA_NUMBER

        try:
            self.camera_width = int(self.camera_width)
        except ValueError:
            self.camera_width = DEFAULT_CAMERA_WIDTH

        try:
            self.camera_height = int(self.camera_height)
        except ValueError:
            self.camera_height = DEFAULT_CAMERA_HEIGHT

    def _save_to_file(self, file):
        """ Save the options to the specified file. """
        self._clean_values()
        line = "{}" + DELIMITER + "{}\n"

        with open(file, 'w') as f:
            f.write(line.format(TAG_STORE_DIRECTORY, self.store_directory))
            f.write(line.format(TAG_SLOT_IMAGES, self.slot_images))
            f.write(line.format(TAG_SLOT_IMAGE_DIRECTORY, self.slot_image_directory))
            f.write(line.format(TAG_CAMERA_NUMBER, self.camera_number))
            f.write(line.format(TAG_CAMERA_WIDTH, self.camera_width))
            f.write(line.format(DEFAULT_CAMERA_HEIGHT, self.camera_height))

    def _load_from_file(self, file):
        """ Load options from the specified file. """
        if not os.path.isfile(file):
            self._save_to_file(file)
            return

        with open(file) as f:
            lines = f.readlines()

            for line in lines:
                try:
                    tokens = line.strip().split(DELIMITER)
                    self._parse_line(tokens[0], tokens[1])
                except:
                    pass

        self._clean_values()

    def _parse_line(self, tag, value):
        """ Parse a line from a config file, setting the relevant option. """
        if tag == TAG_SLOT_IMAGES:
            self.slot_images = bool(value)
        elif tag == TAG_SLOT_IMAGE_DIRECTORY:
            self.slot_image_directory = str(value)
        elif tag == TAG_STORE_DIRECTORY:
            self.store_directory = str(value)
        elif tag == TAG_CAMERA_NUMBER:
            self.camera_number = int(value)
