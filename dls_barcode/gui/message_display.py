import time
from PyQt4.QtGui import QLabel, QGroupBox, QVBoxLayout
from PyQt4 import QtCore

from dls_util.message import MessageType

MSG_LIFETIME = 2

class MessageDisplay(QGroupBox):
    """GUI component. Displays messages for the user."""
    RED = "red"
    BLACK = "black"

    def __init__(self):
        super(MessageDisplay, self).__init__()

        self.setTitle("Information")

        self._colors = {MessageType.INFO: "black",
                        MessageType.WARNING: "red"}
        self._init_ui()

        # Start a timer to clear old messages
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._clear_old_message)
        self._timer.start(1000)

    def _init_ui(self):
        self._message_lbl = QLabel()
        self._message_lbl.setStyleSheet("color: red")

        vbox = QVBoxLayout()
        vbox.addWidget(self._message_lbl)
        vbox.addStretch()
        self.setLayout(vbox)

    def display_message(self, message):
        self._message_lbl.setText(message.content())
        self._message_lbl.setStyleSheet("color: " + self._colors[message.type()])
        self._latest_message_time = time.time()

    def _clear_old_message(self):
        now = time.time()
        if self._message_lbl.text() and now - self._latest_message_time > MSG_LIFETIME:
            self._message_lbl.clear()
