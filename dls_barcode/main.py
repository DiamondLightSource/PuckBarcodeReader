import sys

from os.path import dirname
from sys import path
path.append(dirname(path[0]))

# Required for multiprocessing to work under PyInstaller bundling in Windows
from dls_util import multiprocessing_support

from PyQt4 import QtGui
from gui import DiamondBarcodeMainWindow
import argparse

# Detect if the program is running from source or has been bundled
IS_BUNDLED = getattr(sys, 'frozen', False)
if IS_BUNDLED:
    DEFAULT_CONFIG_FILE = "./config.ini"
else:
    DEFAULT_CONFIG_FILE = "../config.ini"


def main(config_file):
    app = QtGui.QApplication(sys.argv)
    ex = DiamondBarcodeMainWindow(config_file)
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Multiprocessing support for PyInstaller bundling in Windows
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config_file", type=str, default=DEFAULT_CONFIG_FILE,
                        help="The path of the configuration file (default=" + DEFAULT_CONFIG_FILE + ")")
    args = parser.parse_args()
    print("CONFIG: " + args.config_file)

    main(args.config_file)
