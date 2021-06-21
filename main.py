from dls_barcode.gui.main_window import DiamondBarcodeMainWindow

import logging
import sys

from os.path import dirname
from sys import path

import cv2
from dls_barcode.config import BarcodeConfig

from dls_barcode.new_main_manager import NewMainManager
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
    
    manager = NewMainManager(config)
    manager.initialise_scanner()
    ui.set_actions_triger( manager)
    #while  len(SIDE_RESULT.barcodes()) == 0:
   # result = scan_result.ScanResult(0)
   # top_result = scan_result.ScanResult(0)

   
    #while  len(result.barcodes()) == 0:
        
     #   result = manager.get_side_result()
      #  if result is not None :
     
       #     ui.displayHolderImage(result.get_frame_image())
        #    if ui.isLatestHolderBarcode(result.barcodes()[0]):
        #        break
         #   else:
          #      while  len(top_result.barcodes()) == 0:
           #         top_result = manager.get_top_result()
                   # ui.displayPuckImage(top_result.get_frame_image())
                
       # ui.addRecordFrame(result.barcodes()[0].data(), top_result.plate(), result.get_frame_image(), top_result.get_frame_image())
 
   # manager.cleanup()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # Multiprocessing support for PyInstaller bundling in Windows
    parser = argparse.ArgumentParser()
    parser.add_argument("-cf", "--config_file", type=str, default=DEFAULT_CONFIG_FILE,
                        help="The path of the configuration file (default=" + DEFAULT_CONFIG_FILE + ")")
    args = parser.parse_args()

    main(args.config_file, VERSION)
