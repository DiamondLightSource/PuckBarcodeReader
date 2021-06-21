from dls_barcode.gui import main_window
from dls_barcode.scan import scan_result
from zipfile import error
import sys

from PyQt5.QtCore import QMutex, QObject, pyqtSignal

from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.camera.new_camera_switch import NewCameraSwitch
from dls_barcode.camera.plate_overlay import PlateOverlay
from dls_barcode.camera.stream_manager import StreamManager
from dls_barcode.gui.message_factory import MessageFactory



class NewMainManager:

    def __init__(self, config):
        self._config = config 
        self.side_camera_stream = None
        self.top_camera_stream = None

    def get_camera_configs(self):
        return self._camera_configs
    
    def initialise_scanner(self): 

        self.side_camera_stream = StreamManager(self._config.get_side_camera_config(), CameraPosition.SIDE)
        self.side_camera_stream.initialise_stream()
        self.side_camera_stream.create_capture()
        self.side_camera_stream.create_scanner(self._config)
        
        #side_camera_stream.release_capture()
        self.top_camera_stream = StreamManager(self._config.get_top_camera_config(), CameraPosition.TOP)
        self.top_camera_stream.initialise_stream()
        self.top_camera_stream.create_capture()
        self.top_camera_stream.create_scanner(self._config)
   
    def cleanup(self):
        self.side_camera_stream.release_capture()
        self.top_camera_stream.release_capture()
        
    
class SideWorker(QObject):
    finished = pyqtSignal()
    new_side_barcode = pyqtSignal()

    def run(self, side_camera_stream, is_running, is_latest_holder_barcode): 
        if is_running:
            main_window.SIDE_RESULT = side_camera_stream.process_frame()
            if len(main_window.SIDE_RESULT.barcodes()) >0 and not is_latest_holder_barcode:
                self.new_side_barcode.emit()

        self.finished.emit()

        
class TopWorker(QObject):
    finished = pyqtSignal()
    #progress = pyqtSignal(int)

    def run(self, top_camera_stream):
        i = 0 
        while i < 3:#len(main_window.TOP_RESULT.barcodes()) == 0:
            main_window.TOP_RESULT = top_camera_stream.process_frame()
            i = i + 1
        self.finished.emit()







      