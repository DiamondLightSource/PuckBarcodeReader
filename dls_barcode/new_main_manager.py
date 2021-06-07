from zipfile import error
import sys
from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.camera.new_camera_switch import NewCameraSwitch
from dls_barcode.camera.plate_overlay import PlateOverlay
from dls_barcode.camera.stream_manager import StreamManager
from dls_barcode.gui.message_factory import MessageFactory

class NewMainManager:

    def __init__(self, config):
        self._config = config 
        self._camera_switch = None
        self._result = None

    def get_camera_configs(self):
        return self._camera_configs
    
    def initialise_scanner(self): 

        self.side_camera_stream = StreamManager(self._config.get_side_camera_config(), CameraPosition.SIDE)
        self.side_camera_stream.initialise_stream()
        self.side_camera_stream.create_capture()
        self.side_camera_stream.create_scanner(self._config)
        
        #side_camera_stream.release_capture()
       # top_camera_stream = StreamManager(self._config.get_top_camera_config(), CameraPosition.TOP)
       # top_camera_stream.initialise_stream()
       # top_camera_stream.create_capture()
       # top_camera_stream.create_scanner(self._config)
       # self._camera_switch = NewCameraSwitch(side_camera_stream, top_camera_stream, self._config.top_camera_timeout)
        #self._result = top_camera_stream.process_frame()
       # top_camera_stream.release_capture()
       # self._camera_switch.restart_live_capture_from_side() # tuple keeps both top and side result 

        
   
    def cleanup(self):
        self._camera_switch = None
        self._result = None
        self.side_camera_stream.release_capture()
        
    def get_result(self):
        self._result = self.side_camera_stream.process_frame()
        return self._result
    




      