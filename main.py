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
    # Start process logger
    process_logger = ProcessLogger.create_global_logger()
    process_logger.start()
    configure_new_process(process_logger.queue)

    log = logging.getLogger(".".join([__name__]))
    log.info("CONFIG: " + config_file)

    app = QtWidgets.QApplication(sys.argv)
    config = BarcodeConfig(config_file, FileManager())
    ui = DiamondBarcodeMainWindow(config, version, None)
    manager = MainManager(ui, config, process_logger)
    manager.initialise_timers()

    log.debug('2) timers initialised')
    manager.initialise_scanner()
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

    main(args.config_file, VERSION)
