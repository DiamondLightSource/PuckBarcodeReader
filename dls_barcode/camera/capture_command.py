from .stream_action import StreamAction
from .camera_position import CameraPosition

class CaptureCommand:
    """Defines a command that can be sent to the capture worker, to stop or start the camera stream"""
    def __init__(self, action, camera_position=None):
        self.action = action
        self.camera_position = camera_position

        if self.action == StreamAction.START and not isinstance(self.camera_position, CameraPosition):
            raise ValueError("Invalid camera position for START command: " + str(camera_position))
