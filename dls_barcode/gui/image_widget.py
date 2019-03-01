from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QLabel

# Resize button in the right corner didn't work correctly for the image
# I had to add a event filter to the class so that the pixmap is scaled when resizing happens.


class ImageWidget(QLabel):

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if source is self and event.type() == QtCore.QEvent.Resize:
            ma = self.pixmap()
            self.setPixmap(ma.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        return QtWidgets.QWidget.eventFilter(self, source, event)