import time

from .camera import CameraStream
from .overlay import Overlay
from dls_util.image import Image

Q_LIMIT = 1

# Maximum frame rate to sample at (rate will be further limited by speed at which frames can be processed)
MAX_SAMPLE_RATE = 10.0
INTERVAL = 1.0 / MAX_SAMPLE_RATE

# TODO: sort out doc string
class CaptureWorker:

    def __init__(self, camera_configs):
        print("CAPTURE init")
        self._streams = {}
        for cam_position, cam_config in camera_configs.items():
            self._streams[cam_position] = self._initialise_stream(cam_config)

    def run(self, task_queue, view_queue, overlay_queue, start_queue, stop_queue, kill_queue):
        while kill_queue.empty():
            self._flush_queue(stop_queue)
            if start_queue.empty():
                continue

            # TODO: support change in cam configs
            cam_position = start_queue.get(True)
            print("CAPTURE start: " + str(cam_position))
            self._run_capture(self._streams[cam_position], task_queue, view_queue, overlay_queue, stop_queue)

        # Clean up
        print("CAPTURE kill & cleanup")
        for _, stream in self._streams.items():
            stream.release_resources()

    def _run_capture(self, stream, task_queue, view_queue, overlay_queue, stop_queue):
        # Store the latest image overlay which highlights the puck
        latest_overlay = Overlay(0)
        last_time = time.time()

        display = True
        while stop_queue.empty():
            if display:
                print("--- capture inside loop")
                display = False

            # Capture the next frame from the camera
            print("--- acquiring...")
            frame = stream.get_frame()
            # Add the frame to the task queue to be processed
            # NOTE: the rate at which frames are pushed to the task queue is lower than the rate at which frames are acquired
            if task_queue.qsize() < Q_LIMIT and (time.time() - last_time >= INTERVAL):
                # Make a copy of image so the overlay doesn't overwrite it
                task_queue.put(frame.copy())
                last_time = time.time()

            # All frames (scanned or not) are pushed to the view queue for display
            # Get the latest overlay - it won't be generated from the current frame but it doesn't matter
            while not overlay_queue.empty():
                latest_overlay = overlay_queue.get(False)

            # Draw the overlay on the frame
            latest_overlay.draw_on_image(frame)

            view_queue.put(Image(frame))

        print("CAPTURE stop & flush queues")
        self._flush_queue(task_queue)
        self._flush_queue(view_queue)

    def _initialise_stream(self, camera_config):
        cam_number = camera_config[0].value()
        width = camera_config[1].value()
        height = camera_config[2].value()
        return CameraStream(cam_number, width, height)

    def _flush_queue(self, queue):
        while not queue.empty():
            queue.get()