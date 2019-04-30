from dls_util.config import ConfigDialog
from .camera_config_control import CameraConfigControl
from .store_directory_config_control import StoreDirectoryConfigControl

from PyQt5.QtWidgets import QStyle


class BarcodeConfigDialog(ConfigDialog):
    """ Dialog to edit the configuration options for the program. Provides a custom control for
    setting up the camera.
    """
    def __init__(self, config, to_run_before_test_camera):
        ConfigDialog.__init__(self, config)
        self._to_run_before_test_camera = to_run_before_test_camera
        self._config_icon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self._init_ui()
        self.finalize_layout()

    def _init_ui(self):
        self.setGeometry(100, 100, 450, 400)

        self.setWindowIcon(self._config_icon)

        self._to_run_before_test_camera()

        cfg = self._config
        add = self.add_item

        camera_top = CameraConfigControl(cfg.get_top_camera_config())
        camera_side = CameraConfigControl(cfg.get_side_camera_config())

        self.start_group("Colors")
        add(cfg.color_ok)
        add(cfg.color_unreadable)
        add(cfg.color_empty)
        add(cfg.color_accept)

        self.start_group("Top Camera")
        add(cfg.top_barcode_size)
        add(cfg.plate_type)
        add(cfg.top_camera_timeout)
        self._add_control(camera_top)

        self.start_group("Side Camera")
        self._add_control(camera_side)

        self.start_group("Scanning")
        add(cfg.scan_beep)
        add(cfg.scan_clipboard)

        self.start_group("Result Image")
        add(cfg.image_puck)
        add(cfg.image_pins)
        add(cfg.image_crop)

        self.start_group("Store")
        self._add_control(StoreDirectoryConfigControl(cfg.store_directory))
        add(cfg.backup)
        add(cfg.backup_directory)

        self.start_group("Debug")
        add(cfg.console_frame)
        add(cfg.slot_images)
        add(cfg.slot_image_directory)


