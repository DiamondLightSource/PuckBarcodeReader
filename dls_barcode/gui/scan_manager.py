import time
from dls_barcode.camera import CameraScanner


class ScanManager:

    def __init__(self, config, camera_config, scan_queue, view_queue):
        self._config = config
        self._camera_config = camera_config
        self._scan_queue = scan_queue
        self._view_queue = view_queue

        self._scanner = None
        self._reset_top_scan_timer()

    def stop_live_capture(self):
        print("Stop")
        if self._scanner is not None:
            self._scanner.kill()
            self._scanner = None
            # self.original_plate = None #### TODO
            # self.original_cv_image = None #### TODO
            self._reset_top_scan_timer()

    def restart_live_capture_from_side(self):
        self.stop_live_capture()
        print("Start side")
        self._switch_to_side()
        cfg = self._camera_config.getSideCameraConfig()
        self._start_live_capture(self._camera_config.getSideCameraConfig())

    def restart_live_capture_from_top(self):
        self.stop_live_capture()
        print("Start top")
        self._switch_to_top()
        self._start_top_scan_timer()
        cfg = self._camera_config.getPuckCameraConfig()
        self._start_live_capture(self._camera_config.getPuckCameraConfig())

    def is_side(self):
        return self._is_side

    def is_top_scan_timeout(self):
        now = time.time()
        timeout = self._config.top_camera_timeout.value()
        return (self._top_scan_time_start is not None) and (now - self._top_scan_time_start > timeout)

    def _start_live_capture(self, camera_config):
        """ Starts the process of continuous capture from an attached camera.
        """
        self._scanner = CameraScanner(self._scan_queue, self._view_queue)
        self._scanner.stream_camera(config=self._config, camera_config=camera_config)

    def _switch_to_side(self):
        self._is_side = True

    def _switch_to_top(self):
        self._is_side = False

    def _start_top_scan_timer(self):
        self._top_scan_time_start = time.time()

    def _reset_top_scan_timer(self):
        self._top_scan_time_start = None

