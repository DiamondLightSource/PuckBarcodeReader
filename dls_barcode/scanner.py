from PyQt5.QtCore import  QObject, pyqtSignal

from dls_util.cv.frame import Frame
from datetime import datetime


class Scanner(QObject):
    finished = pyqtSignal()
    new_side_frame = pyqtSignal(Frame)
    new_top_frame = pyqtSignal(Frame)
    images_collected = pyqtSignal(Frame, Frame)
    camera_error = pyqtSignal()
    start_time_signal = pyqtSignal()
    stop_time_signal = pyqtSignal()
    success_stop_time_signal = pyqtSignal()
    
    def __init__(self, side_camera_stream, top_camera_stream, duration):
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        # run flag is used to stop the main scan loop in a clean way
        self._run_flag = True
        self._duration = duration
        # start time flag is used in tiemout calculation
        self._start_time = None
        # flag used to pass the information from the processing thread - there is additional logic in mian_widnow ???
        self._new_side_code = False
        # flag used  in the stop time - to make sure stop time is emmited only once 
        self._stop_emitted = False
        # flag used to pass information from the processing thread - to distinguish between timeout scan and successful one ???
        self._successful_scan = False
        # flag used by to pass information from the processin thread - to shorten the scan duration if scan is successfull earlier ???
        self._full_and_valid = False

    def run(self): 
        while self._run_flag: 
            side_frame = self._side_camera_stream.get_frame()
            if side_frame is not None:
                self.new_side_frame.emit(side_frame)
            else:
                self.camera_error.emit()
                break
            top_frame = self._top_camera_stream.get_frame()
            if top_frame is not None:
                self.new_top_frame.emit(top_frame)
            else:
                self.camera_error.emit()
                break
            if top_frame is not None and side_frame is not None: 
                self.images_collected.emit(side_frame, top_frame)
                self.start_time()
                self.stop_time()
                                    
        self.finished.emit()
   
    def stop(self):
        self._run_flag = False
        
    def set_new_side_code(self):
        print("setting new side code")
        if not self._new_side_code:
            self._new_side_code = True
        
    def set_successful_scan(self):
        self._successful_scan = True
        
    def set_full_and_valid_scan(self):
        self._full_and_valid = True
    
    def start_time(self):
        if self._new_side_code:
            self._start_time = datetime.now()
            self.start_time_signal.emit()
            self._new_side_code = False
            self._stop_emitted = False
            self._successful_scan = False
            self._full_and_valid = False
      
    def stop_time(self):
        if self._time_run_out():
            if not self._stop_emitted:
                if self._successful_scan:
                    self.success_stop_time_signal.emit()
                else:
                    self.stop_time_signal.emit()
                self._stop_emitted = True
            
    def _time_run_out(self):
        if self._start_time is None:
            return False
        if self._full_and_valid: # take a shortcut when full and valid 
            print("FULL")
            return True
       
        return (datetime.now() - self._start_time).total_seconds() > self._duration
        

