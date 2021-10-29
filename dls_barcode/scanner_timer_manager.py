from PyQt5.QtCore import  QObject, pyqtSignal

from dls_barcode.scanner_timer import ScannerTimer

class ScannerTimerManager(QObject):
    start_time_signal = pyqtSignal()
    stop_time_signal = pyqtSignal()
    success_stop_time_signal = pyqtSignal()
    
    def __init__(self, duration):
        super().__init__()
        self._scanner_timer = ScannerTimer(self._duration)
         # flag used to pass the information from the processing thread - there is additional logic in mian_widnow ???
        self._new_side_code = False
         # flag used to pass information from the processing thread - to distinguish between timeout scan and successful one ???
        self._successful_scan = False
        # flag used by to pass information from the processin thread - to shorten the scan duration if scan is successfull earlier ???
        self._full_and_valid = False 
        # flag used  in the stop time - to make sure stop time is emmited only once 
        # self._stop_emitted = False
        
    def start_time(self):
        if self._new_side_code:
            self._scanner_timer.start_timer()
            self.start_time_signal.emit()
            self._new_side_code = False
            self._successful_scan = False
            self._full_and_valid = False
      
    def stop_time(self):
        if self._time_run_out():
            if self._successful_scan:
                self.success_stop_time_signal.emit()
            else:
                self.stop_time_signal.emit()
                
    def set_new_side_code(self):
        print("setting new side code")
        if not self._new_side_code:
            self._new_side_code = True
        
    def set_successful_scan(self):
        self._successful_scan = True
        
    def set_full_and_valid_scan(self):
        self._full_and_valid = True
       
    def _time_run_out(self): 
        if self._full_and_valid or self._scanner_timer.time_run_out(): # take a shortcut when full and valid 
            return True
        return False
    