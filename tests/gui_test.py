import sys
from PyQt4 import QtGui, QtCore


class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):
        qbtn = QtGui.QPushButton('Quit', self)
        qbtn.clicked.connect(QtCore.QCoreApplication.instance().quit)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Quit button')
        self.show()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

#     from __future__ import division
#
#     import sys
#
#     from PyQt4 import QtGui, QtCore
#     from PyQt4.QtGui import QGroupBox
#
#
#     class BarcodeTable(QGroupBox):
#         """ GUI component. Displays a list of barcodes for the currently selected puck.
#         """
#
#         def __init__(self):
#             super(BarcodeTable, self).__init__()
#
#             self.setTitle("Barcodes")
#             self._init_ui()
#
#         def _init_ui(self):
#             # Clipboard button - copy the selected barcodes to the clipboard
#             self._btn_clipboard = QtGui.QPushButton('Copy To Clipboard', self)
#             self._btn_clipboard.setToolTip('Copy barcodes for the selected record to the clipboard')
#             self._btn_clipboard.clicked.connect(QtCore.QCoreApplication.instance().quit)
#             self._btn_clipboard.resize(self._btn_clipboard.sizeHint())
#             self._btn_clipboard.setEnabled(True)
#
#             self.setGeometry(300, 300, 250, 150)
#             self.setWindowTitle('Quit button')
#
#             self.show()
#
#
#     def main():
#         app = QtGui.QApplication(sys.argv)
#         ex = BarcodeTable()
#         sys.exit(app.exec_())
#
#
#     if __name__ == '__main__':
#        main()