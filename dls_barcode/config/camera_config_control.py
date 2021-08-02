import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QPushButton, QComboBox
from PyQt5.uic.properties import QtCore

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
        vbox.addLayout(hbox_buttons)

        self.setLayout(vbox)

    def update_from_config(self):
        self.txt_number.setText(str(self._camera_config.get_number()))

    def save_to_config(self):
        self._camera_config.set_number(self.txt_number.text())

    def _test_camera(self):
        self.save_to_config()
        self._test_camera_settings()
        self._display_camera_preview()

    def _open_camera_controls(self):
        camera_num = int(self.txt_number.text())
        CaptureManager.open_camera_controls(camera_num)

    def _test_camera_settings(self):
        # Check that we can connect to the camera
        stream = CaptureManager(self._camera_config)
        stream.create_capture()
        stream.read_frame()
        read_ok = stream.is_read_ok()
        stream.release_resources()
        if not read_ok:
            # Capture the next frame from the camera
            QMessageBox.critical(self, "Camera Error", "Cannot find specified camera")
            return

    def _display_camera_preview(self):
        stream = CaptureManager(self._camera_config)
        stream.create_capture()
        while True:
            stream.read_frame()
            if stream.is_read_ok():
                res = stream.get_frame().get_frame()
                if res is not None:
                    small = res
                    cv2.imshow('Camera Preview', small)
                    cv2.waitKey(50)
            if cv2.getWindowProperty('Camera Preview', 0) < 0:
                break
            
        cv2.destroyAllWindows()
        stream.release_resources()