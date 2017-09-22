from .stream_action import StreamAction


class CaptureCommand:
    """Defines a command that can be sent to the capture worker, to stop or start the camera stream"""
    def __init__(self, action, camera_position=None):
        self._action = action
        self._camera_position = None

        if self._action == StreamAction.START:
            if camera_position is None:
                raise ValueError("Invalid camera position for START command: " + str(camera_position))

            self._camera_position = camera_position

    def get_action(self):
        return self._action

    def get_camera_position(self):
        return self._camera_position
