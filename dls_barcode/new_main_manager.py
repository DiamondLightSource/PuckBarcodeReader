import time
from zipfile import error
from PyQt5 import QtCore

from PyQt5.QtCore import QMutex, QObject, QThread, pyqtSignal

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
        
    
class SideWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(ScanResult)
    new_frame =  pyqtSignal(Frame)
    
    def __init__(self, side_camera_stream) -> None:
        super().__init__()
        self._run_flag = True
        self.side_camera_stream = side_camera_stream

    def run(self): 
        while self._run_flag:
            frame = self.side_camera_stream.get_frame()
            if frame is not None:
                self.new_frame.emit(frame)
                result = self.side_camera_stream.process_frame(frame)
                self.result.emit(result)
        self.finished.emit()
        
    def stop(self):
        self._run_flag = False
    
class TopWorker(QObject):
    finished = pyqtSignal()
    new_frame =  pyqtSignal(Frame)
    
    def __init__(self, top_camera_stream) -> None:
        super().__init__()
        self._run_flag = True
        self.top_camera_stream = top_camera_stream
        self._frame =None

    def run(self):
        while self._run_flag:
            self._frame = self.top_camera_stream.get_frame()
            if self._frame is not None:
                self.new_frame.emit(self._frame)
               
        self.finished.emit()


    def stop(self):
        self._run_flag = False
        
class TopProcessor(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(ScanResult, ScanResult)
    
    def __init__(self, top_camera_stream, timeout, side_result) -> None:
        super().__init__()
        self._run_flag = True
        self.top_camera_stream = top_camera_stream
        self._timeout = timeout
        self.side_result = side_result


    def run(self):
        self._start_time()
        
    def process_frame(self, frame):
        while self._run_flag:
            result = self.top_camera_stream.process_frame(frame)
            self.result.emit(self.side_result, result)
               
        self.finished.emit()
        
        
    def _start_time(self):
        now = time.time()
        self._run_flag = True
        finish = now + self._timeout
        t = now
        print("Processing top")
        while t < finish:
            t = t+1
        print("Finished processing top")
        self._run_flag = False
            

    def stop(self):
        self._run_flag = False
        