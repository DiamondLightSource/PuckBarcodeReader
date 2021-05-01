import logging
import sys

from os.path import dirname
from sys import path
import pygelf
import logconfig
from dls_barcode.config import BarcodeConfig
from dls_barcode.gui import DiamondBarcodeMainWindow
from dls_barcode.new_main_manager import NewMainManager
from PyQt5 import QtWidgets
import argparse
from dls_barcode.version import VERSION
from dls_util.file import FileManager
from dls_util.logging.process_logging import configure_new_process, ProcessLogger

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
    manager = NewMainManager(ui, config)
    manager.initialise_scanner()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Multiprocessing support for PyInstaller bundling in Windows
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config_file", type=str, default=DEFAULT_CONFIG_FILE,
                        help="The path of the configuration file (default=" + DEFAULT_CONFIG_FILE + ")")
    args = parser.parse_args()

    main(args.config_file, VERSION)
