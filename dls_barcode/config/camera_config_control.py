import cv2
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QPushButton

from dls_util.config import ConfigControl
from dls_util.cv.capture_manager import CaptureManager


class CameraConfigControl(ConfigControl):
    RES_TEXT_WIDTH = 50
    BUTTON_WIDTH = 150

    def __init__(self, camera_config):
        ConfigControl.__init__(self, camera_config)
        self._camera_config = camera_config
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
        self.txt_number.setText(str(self._camera_config.get_number()))
        self.txt_width.setText(str(self._camera_config.get_width()))
        self.txt_height.setText(str(self._camera_config.get_height()))

    def save_to_config(self):
        self._camera_config.set_number(self.txt_number.text())
        self._camera_config.set_width(self.txt_width.text())
        self._camera_config.set_height(self.txt_height.text())

    def _test_camera(self):
        self.save_to_config()
        self._test_camera_settings()
        self._display_camera_preview()

    def _open_camera_controls(self):
        camera_num = int(self.txt_number.text())
        CaptureManager.open_camera_controls(camera_num)

    def _test_camera_settings(self):
        # Check that values are integers
        values_int = self._camera_config.values_are_int()

        if not values_int:
            QMessageBox.critical(self, "Camera Error", "Camera number, width, and height must be integers")
            return

        # Check that we can connect to the camera
        stream = CaptureManager(self._camera_config)
        stream.create_capture()
        stream.read_frame()
        read_ok = stream.is_read_ok()
        set_width = int(stream.get_width())
        set_height = int(stream.get_height())
        stream.release_resources()
        if not read_ok:
            # Capture the next frame from the camera
            QMessageBox.critical(self, "Camera Error", "Cannot find specified camera")
            return

        # Check resolution is acceptable - change this!!!
        if set_width != self._camera_config.get_width() or set_height != self._camera_config.get_height():
            QMessageBox.warning(self, "Camera Error",
                            "Could not set the camera to the specified resolution: {}x{}.\nThe camera defaulted "
                            "to {}x{}.".format(self._camera_config.get_width(),
                                               self._camera_config.get_height(), set_width, set_height))
            self.txt_width.setText(str(set_width))
            self.txt_height.setText(str(set_height))
            self.save_to_config()
            return

    def _display_camera_preview(self):
        stream = CaptureManager(self._camera_config)
        stream.create_capture()
        while True:
            stream.read_frame()
            res = stream.get_frame()
            if res is not None:
                small = cv2.resize(res, (0, 0), fx=0.5, fy=0.5)
                cv2.imshow('Camera Preview', small)
                cv2.waitKey(50)
            if cv2.getWindowProperty('Camera Preview', 0) <0:
                break
        cv2.destroyAllWindows()
        stream.release_resources()
