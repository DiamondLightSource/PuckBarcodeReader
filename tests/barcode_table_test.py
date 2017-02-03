from __future__ import division

import os


import sys

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QGroupBox, QVBoxLayout, QHBoxLayout, QTableWidget

from dls_barcode.config import BarcodeConfig
from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL


class BarcodeTable(QtGui.QGroupBox):
    """ GUI component. Displays a list of barcodes for the currently selected puck.
    """
    def __init__(self):
        super(BarcodeTable, self).__init__()

        #self._barcodes = []

        #self._options = options

        self.setTitle("Barcodes")
        self._init_ui()

    def _init_ui(self):
        # Clipboard button - copy the selected barcodes to the clipboard
        self._btn_clipboard = QtGui.QPushButton('Copy To Clipboard', self)
        self._btn_clipboard.setToolTip('Copy barcodes for the selected record to the clipboard')
        self._btn_clipboard.clicked.connect(self.copy_selected_to_clipboard)
        #self._btn_clipboard.clicked.connect(QtCore.QCoreApplication.instance().quit)
        self.setGeometry(300, 300, 250, 150)
        self._btn_clipboard.move(50, 50)
        self.show()

    # def _update_button_state(self):
    #     if self._barcodes is None or len(self._barcodes) == 0:
    #         self._btn_clipboard.setEnabled(False)
    #     else:
    #         self._btn_clipboard.setEnabled(True)
    #
    def copy_selected_to_clipboard(self):
        sep = os.linesep
        if self._barcodes:
            import pyperclip
            pyperclip.copy(sep.join(self._barcodes))

def main():
    app = QtGui.QApplication(sys.argv)
    ex = BarcodeTable()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()