import sys

from os.path import dirname
from sys import path
path.append(dirname(path[0]))

# Required for multiprocessing to work under PyInstaller bundling in Windows
from dls_util import multiprocessing_support

from PyQt4 import QtGui
from gui import DiamondBarcodeMainWindow

# Detect if the program is running from source or has been bundled
IS_BUNDLED = getattr(sys, 'frozen', False)
if IS_BUNDLED:
    CONFIG_FILE = "./config.ini"
else:
    CONFIG_FILE = "../config.ini"


def main():
    app = QtGui.QApplication(sys.argv)
    ex = DiamondBarcodeMainWindow(CONFIG_FILE)
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Multiprocessing support for PyInstaller bundling in Windows
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    main()
