import time
from .camera_position import CameraPosition

class CameraSwitch:
    """Class that handles switching camera streams"""

    def __init__(self, camera_scanner, config):
        self._config = config

        self._scanner = camera_scanner
        self._reset_top_scan_timer()
        self._switch_to_side()

    def stop_live_capture(self):
        self._scanner.stop_scan()
        self._reset_top_scan_timer()

    def restart_live_capture_from_side(self):
        self.stop_live_capture()
        self._switch_to_side()
        self._scanner.start_scan(CameraPosition.SIDE, self._config)

    def restart_live_capture_from_top(self):
        self.stop_live_capture()
        self._switch_to_top()
        self._start_top_scan_timer()
        self._scanner.start_scan(CameraPosition.TOP, self._config)

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

