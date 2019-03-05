from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QGroupBox, QVBoxLayout

BLACK = "; color: black"
BASIC_STYLE_SHEET = "font-size: 25pt"


class CountdownBox(QGroupBox):
    """GUI component. Displays countdown for the user."""

    def __init__(self):
        super(CountdownBox, self).__init__()

        self.setTitle("Countdown")
        self.setMaximumHeight(100)
        self.setMaximumWidth(100)
        self._init_ui()
        self.count = None

    def _init_ui(self):
        self._message_lbl = QLabel()
        self._message_lbl.setStyleSheet(BASIC_STYLE_SHEET + BLACK)
        self._message_lbl.setAlignment(QtCore.Qt.AlignCenter)
        vbox = QVBoxLayout()
        vbox.addWidget(self._message_lbl)
        vbox.addStretch()
        self.setLayout(vbox)

    def start_countdown(self, count):
        self.count = count
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.display)
        self._timer.start(1000)

    def reset_countdown(self):
        self._message_lbl.clear()
        self.count = None

    def display(self):
        self._message_lbl.clear()
        if self.count is not None and self.count >= 0:
            self._message_lbl.setText(str(self.count))
            self.count = self.count - 1
