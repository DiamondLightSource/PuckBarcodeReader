from dls_barcode.scan.scan_result import ScanResult
from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.scan import GeometryScanner, SlotScanner, OpenScanner
from dls_barcode.datamatrix import DataMatrix
from dls_util.cv.capture_manager import CaptureManager

class StreamManager:
    
    def __init__(self, camera_config, cam_position):
        self.camera_config = camera_config
        self.camera_position = cam_position
        self.stream = None
        self._scanner = None 
        
    def initialise_stream(self, ):
        self.stream = CaptureManager(self.camera_config)
        
    def create_capture(self):
        self.stream.create_capture()
        
    def release_capture(self):
        self.stream.release_resources()
        
   # def get_capture(self):
    #    return stream
    
    #def get_camera_position(self):
    #     return self.camera_position
    
    def create_scanner(self,config):
        if self.camera_position == CameraPosition.SIDE:
            plate_type = "None"
            barcode_sizes = DataMatrix.DEFAULT_SIDE_SIZES
        else:
            plate_type = config.plate_type.value()
            barcode_sizes = [config.top_barcode_size.value()]

        if plate_type == "None":
            self._scanner = OpenScanner(barcode_sizes)
        else:
            self._scanner = GeometryScanner(plate_type, barcode_sizes)
            

    def process_frame(self,frame):
        if frame is None:
            return ScanResult(0)
            
        return self._scanner.scan_next_frame(frame)
     
            
    def get_frame(self):
        self.stream.read_frame()
        if self.stream.is_read_ok():
            frame = self.stream.get_frame()
            return frame
        return None
        