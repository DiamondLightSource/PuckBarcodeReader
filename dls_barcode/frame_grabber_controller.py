from PyQt5.QtCore import QObject, QThread, pyqtSlot
from dls_barcode.frame_grabber import FrameGrabber
from dls_barcode.frame_processor_controller import FrameProcessorController
from dls_barcode.scanner_manager import ScannerManager


from dls_util.cv.frame import Frame


class FrameGrabberController(QObject):
    
    def __init__(self, config, displayPuckScanCompleteMessage, displayScanTimeoutMessage, is_latest_holder_barcode,
                 startCountdown, addRecordFrame, clear_frame, scanCompleted):
        super().__init__()
        self.grabber_thread = QThread()
        self.grabber_worker = None
        self._manager = ScannerManager(config)
        self._processor_controller = FrameProcessorController(self._manager, config, displayPuckScanCompleteMessage, 
                                                              displayScanTimeoutMessage, is_latest_holder_barcode,
                                                              startCountdown, addRecordFrame, clear_frame, scanCompleted )
        
    def start_grabber_thread(self, displayHolderFrame, displayPuckFrame, displayCameraErrorMessage):
        self.grabber_thread = QThread()
        self._manager.initialise_scanner()
        self.grabber_worker = FrameGrabber(self._manager.side_camera_stream, self._manager.top_camera_stream)
        self.grabber_worker.moveToThread(self.grabber_thread)
        self.grabber_thread.started.connect(self.grabber_worker.run)
        self.grabber_worker.new_side_frame.connect(displayHolderFrame)
        self.grabber_worker.new_top_frame.connect(displayPuckFrame)
        self.grabber_worker.finished.connect(self.grabber_worker.deleteLater)   
        self.grabber_thread.finished.connect(self.grabber_worker.deleteLater) 
        self.grabber_worker.finished.connect(self.grabber_thread.quit)
        self.grabber_worker.images_collected.connect(self.start_processor)
        self.grabber_worker.camera_error.connect(displayCameraErrorMessage)
        self.grabber_thread.start()
            
    def kill_grabber_thread(self):
        if self.grabber_worker is not None:
            self.grabber_worker.stop()     
        self.grabber_thread.quit()
        self.grabber_thread.wait()
        self._manager.cleanup()

    @pyqtSlot(Frame, Frame)
    def start_processor(self, side_frame, top_frame):   
        self._processor_controller.start_processor(side_frame, top_frame)

