import os

from dls_barcode.util.image import Image

TAG_STORE_DIRECTORY = "store_dir"
TAG_SLOT_IMAGES = "slot_images"
TAG_SLOT_IMAGE_DIRECTORY = "slot_img_dir"

DELIMIT = "="
END = "\n"


class ProgramOptions:
    def __init__(self, file):
        self._file = file

        self.colour_ok = Image.GREEN
        self.color_not_found = Image.RED
        self.color_unreadable = Image.ORANGE

        self.store_directory = "../store/"
        self.slot_images = False
        self.slot_image_directory = "../debug-output/"

        self._load_from_file(file)

    def update_config_file(self):
        """ Save the options to the config file. """
        self._save_to_file(self._file)

    def _clean_values(self):
        self.store_directory = self.store_directory.strip()
        self.slot_image_directory = self.slot_image_directory.strip()

        if not self.store_directory.endswith("/"):
            self.store_directory += "/"

        if not self.slot_image_directory.endswith("/"):
            self.slot_image_directory += "/"

    def _save_to_file(self, file):
        """ Save the options to the specified file. """
        self._clean_values()
        line = "{}" + DELIMIT + "{}" + END

        with open(file, 'w') as f:
            f.write(line.format(TAG_STORE_DIRECTORY, self.store_directory))
            f.write(line.format(TAG_SLOT_IMAGES, self.slot_images))
            f.write(line.format(TAG_SLOT_IMAGE_DIRECTORY, self.slot_image_directory))

    def _load_from_file(self, file):
        """ Load options from the specified file. """
        if not os.path.isfile(file):
            self._save_to_file(file)
            return

        with open(file) as f:
            lines = f.readlines()

            for line in lines:
                try:
                    tokens = line.strip().split("=")
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
