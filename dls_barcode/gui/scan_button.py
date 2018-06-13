from __future__ import division

from PyQt4.QtCore import QTime, QTimer
from PyQt4.QtGui import QPushButton, QGroupBox, QVBoxLayout, QStyle


class ScanButton(QGroupBox):
    """ GUI component. Displays a start/stop button
    """
    def __init__(self, title):
        super(ScanButton, self).__init__()
        self._start_capture_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self._stop_capture_icon = self.style().standardIcon(QStyle.SP_MediaStop)
        self.setTitle(title)

        self._init_ui()

    def _init_ui(self):
        self._scan_button = QPushButton('')
        self._scan_button.setShortcut('Ctrl+W')
        self._scan_button.setStatusTip('Capture continuously from camera')

        self._scan_button.setMaximumWidth(100)

        self.setStopLayout()
        vbox = QVBoxLayout()
        vbox.addWidget(self._scan_button)
        self.setLayout(vbox)

    # A small delay in the button layout change - process restart is slow at the moment
    def setDelayedStopLayout(self):
        self._scan_button.setDisabled(True)
        timer = QTimer()
        timer.singleShot(6000, self.setStopLayout) # 6sec delay

    def setStopLayout(self):
        self._scan_button.setIcon(self._stop_capture_icon)
        self._scan_button.setStyleSheet("background-color: rgb(255, 0, 0)")
        self._scan_button.setDisabled(False)

    def setStartLayout(self):
        self._scan_button.setIcon(self._start_capture_icon)
        self._scan_button.setStyleSheet("background-color: rgb(0, 255, 0)")

    def click_action(self, on_scan_action_clicked):
        self._scan_button.clicked.connect(on_scan_action_clicked)