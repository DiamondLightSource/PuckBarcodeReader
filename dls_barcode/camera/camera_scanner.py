from __future__ import division

import multiprocessing
import queue
import logging

from .capture_worker import CaptureWorker
from .scanner_worker import ScannerWorker
from .camera_position import CameraPosition
from .stream_action import StreamAction
from .capture_command import CaptureCommand


class CameraScanner:
    """ Manages the continuous scanning mode which takes a live feed from an attached camera and
    periodically scans the images for plates and barcodes. Multiple partial images are combined
    together until enough barcodes are scanned to make a full plate.

    Two separate processes are spawned, one to handle capturing and displaying images from the cameras,
    and the other to handle processing (scanning) of those images.
    """
    def __init__(self, result_queue, view_queue, message_queue, config):
        """ The task queue is used to store a queue of captured frames to be processed; the overlay
        queue stores Overlay objects which are drawn on to the image displayed to the user to highlight
        certain features; and the result queue is used to pass on the results of successful scans to
        the object that created the scanner.
        """
        self._task_q = multiprocessing.Queue()
        self._overlay_q = multiprocessing.Queue()
        self._capture_command_q = multiprocessing.Queue()
        self._capture_kill_q = multiprocessing.Queue()
        self._scanner_kill_q = multiprocessing.Queue()
        self._result_q = result_queue
        self._view_q = view_queue
        self._message_q = message_queue

        self._config = config
        self._camera_configs = {CameraPosition.SIDE: self._config.get_side_camera_config(),
                                CameraPosition.TOP: self._config.get_top_camera_config()}

        capture_args = (self._task_q, self._view_q, self._overlay_q, self._capture_command_q, self._capture_kill_q, self._message_q,
                        self._camera_configs)

        # The capture process is always running: we initialise the cameras only once because it's time consuming
        self._capture_process = multiprocessing.Process(target=CameraScanner._capture_worker, args=capture_args)
        self._capture_process.start()

        self._scanner_process = None

    def start_scan(self, cam_position):
        """ Spawn the processes that will continuously capture and process images from the camera.
        """
        log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        log.debug("8) scan start triggered")
        scanner_args = (self._task_q, self._overlay_q, self._result_q, self._message_q, self._scanner_kill_q, self._config, cam_position)
        self._scanner_process = multiprocessing.Process(target=CameraScanner._scanner_worker, args=scanner_args)

        self._capture_command_q.put(CaptureCommand(StreamAction.START, cam_position))
        self._scanner_process.start()

    def stop_scan(self):
        log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        log.debug("stop triggered")
        self._terminate_scanner_process()
        self._capture_command_q.put(CaptureCommand(StreamAction.STOP))
        log.debug("stop scan completed")

    def kill(self):
        log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        log.debug("Kill")
        self.stop_scan()
        self._capture_kill_q.put(None)
        log.debug("KILL forcing capture cleanup")
        self._process_cleanup(self._capture_process, [self._task_q, self._view_q])
        self._capture_process.join()
        self._flush_queue(self._capture_kill_q)
        log.debug("KILL COMPLETED")

    def _flush_queue(self, queue):
        while not queue.empty():
            queue.get()

    def _terminate_scanner_process(self):
        if self._scanner_process is not None:
            self._scanner_kill_q.put(None)
            log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
            log.debug("starting scanner process cleanup")
            self._process_cleanup(self._scanner_process, [self._result_q, self._overlay_q, self._message_q])
            self._scanner_process.join()
            self._flush_queue(self._scanner_kill_q)
            self._scanner_process = None
            log.debug("scanner process cleared and rejoined - caused by stop scan")

    def _process_cleanup(self, process, queues):
        """ A sub-process that writes to a queue can't terminate if the queue is not empty.
            I have tried letting the sub-processes empty the queues by relying on queue.empty() but this method
            may indicate that a queue is empty when in fact it's not, and the processes can't terminate!
            Here we keep trying to empty the queues until the process is dead.
            This was adapted from:
            https://stackoverflow.com/questions/31708646/process-join-and-queue-dont-work-with-large-numbers
        """
        # Put the process in a list so we don't need to check is_alive() every time - supposed to perform better
        log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        live_processes = [process]
        display = True
        while live_processes:
            if display:
                log.debug("scanner process still alive")
                display = False

            for q in queues:
                try:
                    while True:
                        q.get(False)
                except queue.Empty:
                    pass

            if not all(q.empty() for q in queues):
                continue

            live_processes = [p for p in live_processes if p.is_alive()]

        log.debug("scanner process terminated by process cleanup")

    @staticmethod
    def _capture_worker(task_queue, view_queue, overlay_queue, command_queue, kill_queue, message_queue, camera_configs):
        """ Function used as the main loop of a worker process.
        """
        #try:
        CaptureWorker(camera_configs).run(task_queue, view_queue, overlay_queue, command_queue, kill_queue, message_queue)
        #except IOError:
        #    raise message_queue.IOError


    @staticmethod
    def _scanner_worker(task_queue, overlay_queue, result_queue, message_queue, kill_queue, config, cam_position):
        """ Function used as the main loop of a worker process.
        """
        ScannerWorker().run(task_queue, overlay_queue, result_queue, message_queue, kill_queue, config, cam_position)
