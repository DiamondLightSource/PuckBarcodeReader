from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QGroupBox, QVBoxLayout, QProgressBar

BLACK = "; color: black"
BASIC_STYLE_SHEET = "font-size: 20pt"


class ProgressBox(QGroupBox):
    """GUI component. Displays countdown for the user."""

    def __init__(self):
        super(ProgressBox, self).__init__()

        self.setTitle("Scan Completed")
        self.setMaximumHeight(100)
        self.setMaximumWidth(200)
        self._timer = None
        self._init_ui()
        self.count = 0

    def _init_ui(self):
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        vbox = QVBoxLayout()
        vbox.addWidget(self.pbar)
        vbox.addStretch()
        self.setLayout(vbox)

    def start_countdown(self, count):
        self.count = 0
        self.pbar.setValue(self.count)
        self.max = count
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.display)
        self._timer.start(1000)

    def reset_countdown(self):
            if self._timer is not None:
                self._timer.stop()
                self._timer = None
            self.count = 0
            self.pbar.setValue(self.count)

    def display(self):
        if self.count <= self.max:
            self.count = self.count + 1
            self.pbar.setValue(100 * (self.count / self.max))

    def scan_completed(self):
        self.count = 100
        self.pbar.setValue(self.count)
