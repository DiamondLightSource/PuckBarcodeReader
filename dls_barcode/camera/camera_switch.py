import time
from .camera_position import CameraPosition

class CameraSwitch:
    """Class that orchestrates switching camera streams"""

    def __init__(self, camera_scanner, timeout_config):
        self._timeout = timeout_config

        self._scanner = camera_scanner
        self._reset_top_scan_timer()
        self._switch_to_side()

    def _stop_live_capture(self):
        self._scanner.stop_scan()
        self._reset_top_scan_timer()

    def restart_live_capture_from_side(self):
        self._stop_live_capture()
        self._switch_to_side()
        self._scanner.start_scan(CameraPosition.SIDE)

    def restart_live_capture_from_top(self):
        self._stop_live_capture()
        self._switch_to_top()
        self._start_top_scan_timer()
        self._scanner.start_scan(CameraPosition.TOP)

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

