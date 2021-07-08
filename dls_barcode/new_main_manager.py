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
    new_side_frame = pyqtSignal(Frame)
    new_top_frame = pyqtSignal(Frame)
    
    def __init__(self, side_camera_stream, top_camera_stream, timeout, last_holder_barcode, add_record):
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._timeout = timeout
        self._is_last_holder_barcode = last_holder_barcode
        self._add_record_frame = add_record
        self._run_flag = True
        self._stop_flag  = False
    
    def run(self): 
        self.processor_thread = QThread()
        while self._run_flag:
            
            side_frame = self._side_camera_stream.get_frame()
            if side_frame is not None:
                self.new_side_frame.emit(side_frame)
            top_frame = self._top_camera_stream.get_frame()
            if top_frame is not None:
                self.new_top_frame.emit(top_frame)
            #print( self.processor_thread.isRunning())
            print(self._stop_flag)
            if top_frame is not None and side_frame is not None and not self._stop_flag:
                   
                #self.processor_thread = QThread()
               
                print('createda new processor')
                self.processor_worker = Processor(self._side_camera_stream, self._top_camera_stream, side_frame, top_frame, self._is_last_holder_barcode,self._add_record_frame)
                self.processor_worker.moveToThread(self.processor_thread)
                self.processor_thread.started.connect(self.processor_worker.run)
                self.processor_worker.finished.connect(self.my_stop)
                self.processor_worker.finished.connect(self.processor_worker.deleteLater)
                self.processor_thread.finished.connect(self.processor_thread.deleteLater)
                self.processor_worker.finished.connect(self.processor_thread.quit)
                self.processor_thread.start()
        self.finished.emit()
   
 #   def _create_processor(self, side_frame, top_frame):

    def my_stop(self):
        self._stop_flag = True
        self.processor_thread.quit()
        self.processor_thread.wait()
       
        
    def stop(self):
        self._run_flag = False
        self.processor_thread.quit()
        self.processor_thread.wait()
        
        
        
class Processor(QObject):
    finished = pyqtSignal()

    
    def __init__(self, side_camera_stream, top_camera_stream, side_frame, top_frame, is_last_holder_barcode, add_record_frame) -> None:
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._top_frame= top_frame
        self._sied_frame = side_frame
        self._is_last_holder_barcode = is_last_holder_barcode
        self._add_record_frame = add_record_frame

    def run(self):
        side_result = self._side_camera_stream.process_frame(self._sied_frame)
        #if not self._is_last_holder_barcode:
        print("new side code")
        top_result = self._top_camera_stream.process_frame(self._top_frame)   
        self._add_record_frame(side_result, top_result)
        print("finshed procesisng")
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
            

    #def stop(self):
     #   self._run_flag = False
        