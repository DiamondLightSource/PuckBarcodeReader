from PyQt4.QtGui import QLabel, QGroupBox, QVBoxLayout
from PyQt4 import QtCore

from dls_util.message import MessageType

RED = "; color: red"
BLACK = "; color: black"
BASIC_STYLE_SHEET = "font-size: 14pt"

class MessageDisplay(QGroupBox):
    """GUI component. Displays messages for the user."""


    def __init__(self):
        super(MessageDisplay, self).__init__()

        self.setTitle("Information")

        self._style_sheets = {MessageType.INFO: BASIC_STYLE_SHEET + BLACK,
                              MessageType.WARNING: BASIC_STYLE_SHEET + RED}
        self._init_ui()

        # Start a timer to clear old messages
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._clear_old_message)
        self._timer.start(1000)

    def _init_ui(self):
        self._message_lbl = QLabel()
        self._message_lbl.setStyleSheet(BASIC_STYLE_SHEET)

        vbox = QVBoxLayout()
        vbox.addWidget(self._message_lbl)
        vbox.addStretch()
        self.setLayout(vbox)

    def display_message(self, message):
        self._message = message
        self._message_lbl.setText(self._message.content())
        self._message_lbl.setStyleSheet(self._style_sheets[self._message.type()])

    def _clear_old_message(self):
        if self._message_lbl.text() and self._message.has_expired():
            self._message_lbl.clear()
            self._message = None
