import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QLineEdit, QPushButton, QComboBox
from PyQt5.uic.properties import QtCore

from dls_util.config import ConfigControl
from dls_util.cv.capture_manager import CaptureManager, get_available_resolutions


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
        self.combo = QComboBox()
        resolutions = get_available_resolutions()
        for resolution in resolutions:
            width = resolution[0]
            height = resolution[1]
            self.combo.addItem(str(width)+"x"+str(height))
            #print(str(self.combo.height()))

        #self.txt_width = QLineEdit()
        #self.txt_width.setFixedWidth(self.RES_TEXT_WIDTH)
        #self.txt_height = QLineEdit()
        #self.txt_height.setFixedWidth(self.RES_TEXT_WIDTH)

        hbox_res = QHBoxLayout()
        hbox_res.setContentsMargins(0, 0, 0, 0)
        hbox_res.addWidget(lbl)
        hbox_res.addWidget(self.combo)
        #hbox_res.addWidget(self.txt_width)
        #hbox_res.addWidget(QLabel("x"))
        #hbox_res.addWidget(self.txt_height)
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
        text = str(self._camera_config.get_width()) + "x" + str(self._camera_config.get_height())
        index = self.combo.findText(text, Qt.MatchExactly)
        if index >= 0:
            self.combo.setCurrentIndex(index)

        #self.txt_width.setText(str(self._camera_config.get_width()))
        #self.txt_height.setText(str(self._camera_config.get_height()))

    def save_to_config(self):
        self._camera_config.set_number(self.txt_number.text())
        text = str(self.combo.currentText())
        sp = text.split("x")
        w = sp[0]
        h = sp[1]
        self._camera_config.set_height(h)
        self._camera_config.set_width(w)

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
        #self._print_possible_resolutions(stream)
        while True:
            stream.read_frame()
            res = stream.get_frame()
            if res is not None:
                small = cv2.resize(res, (0, 0), fx=0.5, fy=0.5)
                cv2.imshow('Camera Preview', small)
                cv2.waitKey(50)
            if cv2.getWindowProperty('Camera Preview', 0) < 0:
                break
        cv2.destroyAllWindows()
        stream.release_resources()

    # def _print_possible_resolutions(self, cm):
    #     i = 0
    #     x_y_list = []
    #     x = 600
    #     y = 400
    #     while i < 1000:
    #         x = x + i
    #         y = y + i
    #         i = i + 1
    #         x1, y1 = cm.set_res(x, y)
    #         if x1 not in x_y_list:
    #             x_y_list.append(x1)
    #             x = x1
    #             y = y1
    #             i = 0
    #             print(str(x1), str(y1))
    #         if len(x_y_list) > 4:
    #             break
    #     print("end")
