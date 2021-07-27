import time
from zipfile import error
from PyQt5 import QtCore

from PyQt5.QtCore import QMutex, QObject, QThread, QTime, QTimer, pyqtSignal,pyqtSlot

from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.camera.new_camera_switch import NewCameraSwitch
from dls_barcode.camera.plate_overlay import PlateOverlay
from dls_barcode.camera.stream_manager import StreamManager
from dls_barcode.gui import main_window
from dls_barcode.gui.message_factory import MessageFactory
from dls_barcode.scan.scan_result import ScanResult
from dls_util.cv.frame import Frame


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
        
class MainWorker(QObject):
    finished = pyqtSignal()
    new_side_frame = pyqtSignal(Frame)
    new_top_frame = pyqtSignal(Frame)
    images_collected = pyqtSignal(Frame, Frame)
    
    def __init__(self, side_camera_stream, top_camera_stream):
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._run_flag = True

    def run(self): 

        while self._run_flag:
            
            side_frame = self._side_camera_stream.get_frame()
            if side_frame is not None:
                self.new_side_frame.emit(side_frame)
            top_frame = self._top_camera_stream.get_frame()
            if top_frame is not None:
                self.new_top_frame.emit(top_frame)
            if top_frame is not None and side_frame is not None:
                self.images_collected.emit(side_frame, top_frame)
                                    
        self.finished.emit()
   
   
    def stop(self):
        self._run_flag = False

class Processor(QObject):
    finished = pyqtSignal()
    side_top_result =pyqtSignal(ScanResult, ScanResult)
    
    def __init__(self, side_camera_stream, top_camera_stream, side_frame, top_frame) -> None:
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._top_frame= top_frame
        self._sied_frame = side_frame
        

    def run(self):
        side_result = self._side_camera_stream.process_frame(self._sied_frame)
        top_result = self._top_camera_stream.process_frame(self._top_frame)   
        self.side_top_result.emit(side_result,top_result)
        self.finished.emit()

        
        
