import time
from zipfile import error
from PyQt5 import QtCore

from PyQt5.QtCore import QMutex, QObject, QThread, pyqtSignal,pyqtSlot

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
    scan_finished = pyqtSignal()
    side_result = pyqtSignal(ScanResult)
    top_result = pyqtSignal(ScanResult)
    
    def __init__(self, side_camera_stream, top_camera_stream, timeout, display_holder, display_pins, last_holder_barcode):
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._timeout = timeout
        self._display_holder = display_holder
        self._display_pins = display_pins
        self._is_last_holder_barcode = last_holder_barcode
        self._run_flag = True
    
    def run(self): 

        self._process_side_thread()
        self._process_top_thread()  
       
      
        self.finished.emit()
        
    @pyqtSlot(Frame)   
    def _process_side_frame(self, frame):
        print("side processed")
        result = self._side_camera_stream.process_frame(frame)
     
        if not self._is_last_holder_barcode(result):
            print("Is not latest true")
            self.side_result.emit(result)
            #self.top_worker.new_frame.connect(self._process_top_frame)
            
    @pyqtSlot(Frame)   
    def _process_top_frame(self, frame):
        #self._start_time()
        print("top process started")
        result = self._top_camera_stream.process_frame(frame)
        #while self._run_flag:
        self.top_result.emit(result)
            
        self.scan_finished.emit()
        
        
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
            
    def _process_side_thread(self):    
        # TODO: change this so that it uses the processes
        self.side_thread = QThread()
        self.side_worker = SideWorker(self._side_camera_stream)
        self.side_worker.moveToThread(self.side_thread)
        self.side_thread.started.connect(self.side_worker.run)
        self.side_worker.finished.connect(self.side_thread.quit)
        self.side_worker.new_frame.connect(self._display_holder)
        self.side_worker.new_frame.connect(self._process_side_frame)
        self.side_thread.start() 
        
    def _process_top_thread(self):
        self.top_worker = TopWorker(self._top_camera_stream)
        self.top_thread = QThread()
        self.top_worker.moveToThread(self.top_thread)
        self.top_thread.started.connect(self.top_worker.run)
        self.top_worker.finished.connect(self.top_thread.quit)
        self.top_worker.new_frame.connect(self._display_pins)
        self.top_worker.new_frame.connect(self._process_top_frame)
        self.top_thread.start() 
   
    def stop(self):
        self._kill_threads()
        self._run_flag = False
        
    def _kill_threads(self):

        if self.side_thread.isRunning():
            self.side_worker.stop()

        if self.top_thread.isRunning():
            self.top_worker.stop() 
        
        #self.side_worker.finished.connect(self.side_worker.deleteLater)
        #self.side_thread.finished.connect(self.side_thread.deleteLater)
        #self.top_worker.finished.connect(self.top_worker.deleteLater)
        #self.top_thread.finished.connect(self.top_thread.deleteLater)
     
class SideWorker(QObject):
    finished = pyqtSignal()

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
        