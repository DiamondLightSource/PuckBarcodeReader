from zipfile import error

from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.camera.new_camera_switch import NewCameraSwitch
from dls_barcode.camera.plate_overlay import PlateOverlay
from dls_barcode.camera.stream_manager import StreamManager
from dls_barcode.gui.message_factory import MessageFactory

class NewMainManager:

    def __init__(self, ui, config):
        self._ui = ui
        self._config = config 
        self._camera_switch = None
        self._result = None
        
        # initialise all actions
        self._ui.set_actions_triger(self._cleanup, self.initialise_scanner)

    def get_camera_configs(self):
        return self._camera_configs
    
    def initialise_scanner(self): 
        side_camera_stream = StreamManager(self._config.get_side_camera_config(), CameraPosition.SIDE)
        side_camera_stream.initialise_stream()
        side_camera_stream.create_capture()
        side_camera_stream.create_scanner(self._config)
        top_camera_stream = StreamManager(self._config.get_top_camera_config(), CameraPosition.TOP)
        top_camera_stream.initialise_stream()
        top_camera_stream.create_capture()
        top_camera_stream.create_scanner(self._config)
        self._camera_switch = NewCameraSwitch(side_camera_stream, top_camera_stream, self._config.top_camera_timeout)

        self._result =  self._camera_switch.restart_live_capture_from_side() # tuple keeps both top and side result 
        
        self._read_view()
        self._read_message()
            
    def _cleanup(self):
        self._camera_switch = None
        self._result = None
        self._ui.resetCountdown()
        
    def _read_view(self):
        top_result = self._result[1]
        if top_result is None:
            return 
        image = top_result.get_frame_image()
 
        self._ui.displayPuckImage(image)
        
    def _read_message(self):
        if self._result[0] is None or self._result[1] is None:
             self._ui.displayCameraErrorMessage(MessageFactory().camera_not_found_message())
