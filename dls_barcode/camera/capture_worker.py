import time
import queue

from dls_util.cv.camera import Camera
from dls_util.cv.camers_manager import CameraManager
from dls_util.image import Overlay
from .scanner_message import CameraErrorMessage, ScanErrorMessage
from .stream_action import StreamAction
from dls_util.image import Image

Q_LIMIT = 1

# Maximum frame rate to sample at (rate will be further limited by speed at which frames can be processed)
MAX_SAMPLE_RATE = 10.0
INTERVAL = 1.0 / MAX_SAMPLE_RATE


class CaptureWorker:
    """Continuously captures images from the camera and puts them on a queue to be processed. The images are displayed
    (as video) to the user with appropriate highlights (taken from the overlay queue) which indicate the position of
    scanned and unscanned barcodes. Cameras are initialised at startup, then the stream is stopped and started to the
    correct camera by reading the command from a start/stop command queue.
    """
    def __init__(self, camera_configs):
        print("CAPTURE init")
        self._streams = {}
        self._camera_configs = camera_configs
        for cam_position, cam_config in self._camera_configs.items():
            self._streams[cam_position] = self._initialise_stream(cam_config)

    def run(self, task_queue, view_queue, overlay_queue, command_queue, kill_queue, message_queue):
        while kill_queue.empty():
            if command_queue.empty():
                continue

            command = command_queue.get()
            if command.get_action() == StreamAction.START:
                camera_position_name = command.get_camera_position_name()
                print("CAPTURE start: " + camera_position_name)
                self._run_capture(self._streams[command.get_camera_position()], camera_position_name, task_queue, view_queue, overlay_queue, command_queue, message_queue)

        # Clean up
        print("CAPTURE kill & cleanup")
        for _, stream in self._streams.items():
            stream.release_resources()

        print("- capture all cleaned")

    def _run_capture(self, stream, camera_positon, task_queue, view_queue, overlay_queue, stop_queue, message_queue):
        # Store the latest image overlay which highlights the puck
        latest_overlay = Overlay(0)
        last_time = time.time()

        display = True
        while stop_queue.empty():
            if display:
                print("--- capture inside loop")
                display = False

            # Capture the next frame from the camera
            try:
                frame = stream.get_frame()
            except IOError:
                message_queue.put(CameraErrorMessage(camera_positon))
                return

            # Add the frame to the task queue to be processed
            # NOTE: the rate at which frames are pushed to the task queue is lower than the rate at which frames are acquired
            if task_queue.qsize() < Q_LIMIT and (time.time() - last_time >= INTERVAL):
                # Make a copy of image so the overlay doesn't overwrite it
                task_queue.put(frame.copy())
                last_time = time.time()

            # All frames (scanned or not) are pushed to the view queue for display
            # Get the latest overlay - it won't be generated from the current frame but it doesn't matter
            while not overlay_queue.empty():
                try:
                    latest_overlay = overlay_queue.get(False)
                except queue.Empty:
                    # Race condition where the scanner worker was stopped and the overlay queue cleared between
                    # our calls to queue.empty() and queue.get(False)
                    latest_overlay = Overlay(0)

            # Draw the overlay on the frame
            latest_overlay.draw_on_image(frame)

            view_queue.put(Image(frame))

        print("CAPTURE stop & flush queues")
        self._flush_queue(task_queue)
        print("--- capture task Q flushed")
        self._flush_queue(view_queue)
        print("--- capture view Q flushed")



    def _initialise_stream(self, camera_config):
        cam_number = camera_config.camera_number.value()
        width = camera_config.width.value()
        height = camera_config.height.value()
        stream = CameraManager(Camera(cam_number, width, height))
        stream.create_capture()
        return stream


    def _flush_queue(self, q):
        while not q.empty():
            try:
                q.get(False)
            except queue.Empty:
                pass