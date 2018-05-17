from __future__ import division


from PyQt4.QtGui import QPushButton, QGroupBox, QVBoxLayout
from PyQt4.QtCore import Qt


class ScanButton(QGroupBox):
    """ GUI component. Displays a start/stop button
    """
    def __init__(self, title, icon_stop, icon_start, on_scan_action_clicked):
        super(ScanButton, self).__init__()
        self._on_scan_action_clicked = on_scan_action_clicked
        self._stop_capture_icon = icon_stop
        self._start_capture_icon = icon_start
        self.setTitle(title)

        self._init_ui()

    def _init_ui(self):
        self._scan_button = QPushButton('')
        self._scan_button.setShortcut('Ctrl+W')
        self._scan_button.setStatusTip('Capture continuously from camera')
        self._scan_button.clicked.connect(self._on_scan_action_clicked)
        self._scan_button.setMaximumWidth(100)

        self.setStopLayout()
        vbox = QVBoxLayout()
        vbox.addWidget(self._scan_button)
        self.setLayout(vbox)

    def setStopLayout(self):
        self._scan_button.setIcon(self._stop_capture_icon)
        self._scan_button.setStyleSheet("background-color: rgb(255, 0, 0)")

    def setStartLayout(self):
        self._scan_button.setIcon(self._start_capture_icon)
        self._scan_button.setStyleSheet("background-color: rgb(0, 255, 0)")
