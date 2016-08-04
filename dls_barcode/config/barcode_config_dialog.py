import cv2
from PyQt4.QtGui import QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QPushButton

from dls_barcode.util import ConfigDialog, ConfigControl


class BarcodeConfigDialog(ConfigDialog):
    """ Dialog to edit the configuration options for the program. Provides a custom control for
    setting up the camera.
    """
    def __init__(self, config):
        ConfigDialog.__init__(self, config)

        self._init_ui()
        self.finalize_layout()

    def _init_ui(self):
        self.setGeometry(100, 100, 450, 400)

        cfg = self._config
        add = self.add_item

        camera = CameraConfigControl(cfg.camera_number, cfg.camera_width, cfg.camera_height)

        self.start_group("Sample Plate")
        add(cfg.plate_type)

        self.start_group("Colors")
        add(cfg.color_ok)
        add(cfg.color_unreadable)
        add(cfg.color_empty)

        self.start_group("Camera")
        self._add_control(camera)

        self.start_group("Scanning")
        add(cfg.scan_beep)
        add(cfg.scan_clipboard)

        self.start_group("Result Image")
        add(cfg.image_puck)
        add(cfg.image_pins)
        add(cfg.image_crop)

        self.start_group("Store")
        add(cfg.store_directory)
        add(cfg.store_capacity)

        self.start_group("Debug")
        add(cfg.console_frame)
        add(cfg.slot_images)
        add(cfg.slot_image_directory)


class CameraConfigControl(ConfigControl):
    RES_TEXT_WIDTH = 50
    BUTTON_WIDTH = 100

    def __init__(self, number_item, width_item, height_item):
        ConfigControl.__init__(self, width_item)
        self._number_item = number_item
        self._width_item = width_item
        self._height_item = height_item
        self._init_ui()

    def _init_ui(self):
        # Set Camera Number
        self.txt_number = QLineEdit()
        self.txt_number.setFixedWidth(self.RES_TEXT_WIDTH)
        lbl_camera_number = QLabel("Camera Number")
        lbl_camera_number.setFixedWidth(ConfigControl.LABEL_WIDTH)

        hbox_num = QHBoxLayout()
        hbox_num.addWidget(lbl_camera_number)
        hbox_num.addWidget(self.txt_number)
        hbox_num.addStretch()

        # Set Camera Resolution
        lbl = QLabel("Camera Resolution")
        lbl.setFixedWidth(ConfigControl.LABEL_WIDTH)
        self.txt_width = QLineEdit()
        self.txt_width.setFixedWidth(self.RES_TEXT_WIDTH)
        self.txt_height = QLineEdit()
        self.txt_height.setFixedWidth(self.RES_TEXT_WIDTH)

        hbox_res = QHBoxLayout()
        hbox_res.setContentsMargins(0, 0, 0, 0)
        hbox_res.addWidget(lbl)
        hbox_res.addWidget(self.txt_width)
        hbox_res.addWidget(QLabel("x"))
        hbox_res.addWidget(self.txt_height)
        hbox_res.addStretch()

        # Preview camera
        btn_camera_test = QPushButton("Test Camera")
        btn_camera_test.setFixedWidth(self.BUTTON_WIDTH)
        btn_camera_test.clicked.connect(self._test_camera)

        btn_camera_settings = QPushButton("Camera Settings")
        btn_camera_settings.setFixedWidth(self.BUTTON_WIDTH)
        btn_camera_settings.clicked.connect(self._open_camera_controls)

        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(btn_camera_test)
        hbox_buttons.addWidget(btn_camera_settings)
        hbox_buttons.addStretch(1)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(hbox_num)
        vbox.addLayout(hbox_res)
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

    def update_from_config(self):
        self.txt_number.setText(str(self._number_item.value()))
        self.txt_width.setText(str(self._width_item.value()))
        self.txt_height.setText(str(self._height_item.value()))

    def save_to_config(self):
        self._number_item.set(self.txt_number.text())
        self._width_item.set(self.txt_width.text())
        self._height_item.set(self.txt_height.text())

    def _test_camera(self):
        # Check that values are integers
        try:
            camera_num = int(self.txt_number.text())
            camera_width = int(self.txt_width.text())
            camera_height = int(self.txt_height.text())
        except ValueError:
            QMessageBox.critical(self, "Camera Error", "Camera number, width, and height must be integers")
            return

        # Check that we can connect to the camera
        cap = cv2.VideoCapture(camera_num)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

        read_ok, _ = cap.read()
        if not read_ok:
            QMessageBox.critical(self, "Camera Error", "Cannot find specified camera")
            return

        # Check resolution is acceptable
        set_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        set_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if set_width != camera_width or set_height != camera_height:
            QMessageBox.warning(self, "Camera Error",
                                "Could not set the camera to the specified resolution: {}x{}.\nThe camera defaulted "
                                "to {}x{}.".format(camera_width, camera_height, set_width, set_height))
            self.txt_width.setText(str(set_width))
            self.txt_height.setText(str(set_height))
            return

        # Display a preview feed from the camera
        breaking_frame = False
        while True:
            # Capture the next frame from the camera
            read_ok, frame = cap.read()

            if frame is None:
                breaking_frame = True
                break
            elif cv2.waitKey(1) != -1:
                break

            small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow('Camera Preview (Press any key to exit)', small)

        cap.release()
        cv2.destroyAllWindows()

        # Opening the camera controls window stops the camera from working; reopen this window
        if breaking_frame:
            self._test_camera()

    def _open_camera_controls(self):
        camera_num = int(self.txt_number.text())
        cap = cv2.VideoCapture(camera_num)
        cap.set(cv2.CAP_PROP_SETTINGS, 1)
