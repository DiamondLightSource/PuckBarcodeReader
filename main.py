from dls_barcode.gui.main_window import DiamondBarcodeMainWindow

import logging
import sys

from os.path import dirname
from sys import path

from dls_barcode.config import BarcodeConfig

from dls_barcode.scanner_manager import ScannerManager
from PyQt5 import QtWidgets
import argparse
from dls_barcode.version import VERSION
from dls_util.file import FileManager

path.append(dirname(path[0]))

# Required for multiprocessing to work under PyInstaller bundling in Windows
from dls_util import multiprocessing_support


# Detect if the program is running from source or has been bundled
IS_BUNDLED = getattr(sys, 'frozen', False)
if IS_BUNDLED:
    DEFAULT_CONFIG_FILE = "./config.ini"
else:
    DEFAULT_CONFIG_FILE = "../config.ini"


def main(config_file, version):
    # Start process logge

    log = logging.getLogger(".".join([__name__]))
    log.info("CONFIG: " + config_file)

    app = QtWidgets.QApplication(sys.argv)
    config = BarcodeConfig(config_file, FileManager())
    ui = DiamondBarcodeMainWindow(config, version, None)
    
    manager = ScannerManager(config)
    manager.initialise_scanner()
    ui.set_actions_triger( manager)

    sys.exit(app.exec_())


if __name__ == '__main__':
    # Multiprocessing support for PyInstaller bundling in Windows
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config_file", type=str, default=DEFAULT_CONFIG_FILE,
                        help="The path of the configuration file (default=" + DEFAULT_CONFIG_FILE + ")")
    args = parser.parse_args()

    main(args.config_file, VERSION)
