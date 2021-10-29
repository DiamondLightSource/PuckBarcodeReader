from datetime import datetime

class ScannerTimer:
        
    def __init__(self, duration):
        self._duration = duration 
        self._start_time = None
        
    def start_timer(self):    
        self._start_time = datetime.now()
            
    def get_duration(self):
        return self._duration
                     
    def time_run_out(self):
        if self._start_time is None:
            return False
        return (datetime.now() - self._start_time).total_seconds() > self._duration
        

    
    