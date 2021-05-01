class NewCameraSwitch:
    
    def __init__(self, side_camera_stream, top_camera_stream, timeout_config):
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self.timeout = timeout_config
        self._reset_top_scan_timer()
        self._switch_to_side()
        
    
    def restart_live_capture_from_side(self): 
        self._switch_to_side()
        side_result = self._side_camera_stream.process_frame()
        top_result = self._top_camera_stream.process_frame()
        return (side_result, top_result)
         
    def restart_live_capture_from_top(self): 
        self._switch_to_top()
        top_result = self._top_camera_stream.process_frame()
        side_result = self._side_camera_stream.process_frame()
        return (side_result, top_result)
           
    def is_side(self):
        return self._is_side

    def get_scan_time(self):
        now = time.time()
        if self._top_scan_time_start is not None:
            return round(now - self._top_scan_time_start, 2)

    def is_top_scan_timeout(self):
        now = time.time()
        return (self._top_scan_time_start is not None) and (now - self._top_scan_time_start > self._timeout.value())

    def _switch_to_side(self):
        self._is_side = True

    def _switch_to_top(self):
        self._is_side = False

    def _start_top_scan_timer(self):
        self._top_scan_time_start = time.time()

    def _reset_top_scan_timer(self):
        self._top_scan_time_start = None
    
        
    
        
    
        