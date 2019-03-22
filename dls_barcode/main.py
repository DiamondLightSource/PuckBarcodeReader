import logging
import sys

from os.path import dirname
from sys import path
import pygelf
import logconfig
from dls_barcode.config import BarcodeConfig
from dls_barcode.gui import DiamondBarcodeMainWindow
from dls_barcode.main_manager import MainManager
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
    app = QtWidgets.QApplication(sys.argv)
    config = BarcodeConfig(config_file, FileManager())
    ui = DiamondBarcodeMainWindow(config, version, None)
    manager = MainManager(ui, config)
    manager.initialise_timers()
    log = logging.getLogger(".".join([__name__]))
    log.debug('2) timers initialised')
    manager.initialise_scanner()
    sys.exit(app.exec_())


if __name__ == '__main__':
    logconfig.setup_logging()
    #logconfig.set_additional_handler("log.log")
    # Multiprocessing support for PyInstaller bundling in Windows
    log = logging.getLogger(".".join([__name__]))
    if sys.platform.startswith('win'):
        import multiprocessing
        multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config_file", type=str, default=DEFAULT_CONFIG_FILE,
                        help="The path of the configuration file (default=" + DEFAULT_CONFIG_FILE + ")")
    args = parser.parse_args()
    log.info("CONFIG: " + args.config_file)
    #print("CONFIG: " + args.config_file)

    main(args.config_file, VERSION)
