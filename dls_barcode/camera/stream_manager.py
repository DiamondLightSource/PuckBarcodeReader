from .camera_scanner import CameraScanner

class StreamManager:
    """Class that stops and starts a camera stream"""
    def __init__(self, scan_queue, view_queue):
        self._scan_queue = scan_queue
        self._view_queue = view_queue
        self._scanner = None

    def start_live_capture(self, config, camera_config):
        """ Starts the process of continuous capture from an attached camera.
        """
        self._scanner = CameraScanner(self._scan_queue, self._view_queue)
        self._scanner.stream_camera(config=config, camera_config=camera_config)

    def stop_live_capture(self):
        if self._scanner is not None:
            self._scanner.kill()
            self._scanner = None


