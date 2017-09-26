import sys

from dls_barcode.geometry import Geometry
from dls_barcode.datamatrix import DataMatrix
from dls_barcode.datamatrix.read import DatamatrixSizeTable
from dls_util.image import Color
from dls_util.config import Config, DirectoryConfigItem, ColorConfigItem, \
    IntConfigItem, BoolConfigItem, EnumConfigItem
from .camera_config import CameraConfig

IS_BUNDLED = getattr(sys, 'frozen', False)


class BarcodeConfig(Config):
    """ Handles configuration options that are used throughout the program. The values are persisted to file
    so that the same values are recalled when the program is restarted.
    """
    def __init__(self, file):
        Config.__init__(self, file)

        add = self.add

        if IS_BUNDLED:
            default_store = "./store/"
        else:
            default_store = "../store/"

        self.color_ok = add(ColorConfigItem, "Read Color", Color.Green())
        self.color_unreadable = add(ColorConfigItem, "Not Read Color", Color.Red())
        self.color_empty = add(ColorConfigItem, "Empty Color", Color.Grey())

        self.plate_type = add(EnumConfigItem, "Sample Plate Type", default=Geometry.UNIPUCK, extra_arg=Geometry.TYPES)
        self.top_barcode_size = add(EnumConfigItem, "Datamatrix Size", default=DataMatrix.DEFAULT_SIZE,
                                    extra_arg=DatamatrixSizeTable.valid_sizes())
        self.top_camera_timeout = add(IntConfigItem, "Scan Timeout", default=60, extra_arg="s")

        self.scan_beep = add(BoolConfigItem, "Beep While Scanning", default=True)
        self.scan_clipboard = add(BoolConfigItem, "Results to Clipboard", default=True)

        self.image_puck = add(BoolConfigItem, "Draw Puck", default=True)
        self.image_pins = add(BoolConfigItem, "Draw Slot Highlights", default=True)
        self.image_crop = add(BoolConfigItem, "Crop to Puck", default=True)

        self.store_directory = add(DirectoryConfigItem, "Startup Store Directory", default=default_store)
        self.store_capacity = add(IntConfigItem, "Results History Size", default=50)

        self.console_frame = add(BoolConfigItem, "Print Frame Summary", default=False)
        self.slot_images = add(BoolConfigItem, "Save Debug Images", default=False)
        self.slot_image_directory = add(DirectoryConfigItem, "Debug Directory", default="../debug-output/")

        self.top_camera_number = add(IntConfigItem, "Top Camera Number", default=1)
        self.top_camera_width = add(IntConfigItem, "Top Camera Width", default=1600)
        self.top_camera_height = add(IntConfigItem, "Top Camera Height", default=1200)

        self.side_camera_number = add(IntConfigItem, "Side Camera Number", default=2)
        self.side_camera_width = add(IntConfigItem, "Side Camera Width", default=1600)
        self.side_camera_height = add(IntConfigItem, "Side Camera Height", default=1200)

        self.initialize_from_file()

    def col_ok(self):
        return self.color_ok.value()

    def col_bad(self):
        return self.color_unreadable.value()

    def col_empty(self):
        return self.color_empty.value()

    def get_top_camera_config(self):
        return CameraConfig(self.top_camera_number, self.top_camera_width, self.top_camera_height)

    def get_side_camera_config(self):
        return CameraConfig(self.side_camera_number, self.side_camera_width, self.side_camera_height)



