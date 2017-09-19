import time
from .stream_manager import StreamManager

class CameraSwitch:
    """Class that handles switching camera streams"""

    def __init__(self, config, stream_manager, camera_config):
        self._config = config
        self._camera_config = camera_config

        self._stream = stream_manager
        self._reset_top_scan_timer()

    def stop_live_capture(self):
        print("Stop")
        self._stream.stop_live_capture()
        self._reset_top_scan_timer()

    def restart_live_capture_from_side(self):
        self.stop_live_capture()
        print("Start side")
        self._switch_to_side()
        self._stream.start_live_capture(self._config, self._camera_config.getSideCameraConfig())

    def restart_live_capture_from_top(self):
        self.stop_live_capture()
        print("Start top")
        self._switch_to_top()
        self._start_top_scan_timer()
        self._stream.start_live_capture(self._config, self._camera_config.getPuckCameraConfig())

    def is_side(self):
        return self._is_side

    def is_top_scan_timeout(self):
        now = time.time()
        timeout = self._config.top_camera_timeout.value()
        return (self._top_scan_time_start is not None) and (now - self._top_scan_time_start > timeout)

    def _switch_to_side(self):
        self._is_side = True

    def _switch_to_top(self):
        self._is_side = False

    def _start_top_scan_timer(self):
        self._top_scan_time_start = time.time()

    def _reset_top_scan_timer(self):
        self._top_scan_time_start = None

