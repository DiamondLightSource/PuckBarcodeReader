from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSlot
from dls_barcode.frame_processor import SideProcessor, TopProcessor
from dls_barcode.scan.scan_result import ScanResult


class FrameProcessorController(QObject):
    
    def __init__(self, manager, config, displayPuckScanCompleteMessage, displayScanTimeoutMessage, is_latest_holder_barcode, 
                 startCountdown, addRecordFrame, clear_frame, scanCompleted):
        super().__init__()
        self.side_processor_thread = QThread() 
        self.top_processor_thread = QThread()
        self._duration = config.get_top_camera_tiemout()
        self._manager = manager
        self.timer = QTimer()
        self.timer.setSingleShot(True) #timer which fies only once 
        self.timer.timeout.connect(self._on_time_out)
        self._side_result = None
        self._top_result = None
        self.processing_flag = False
        # UI funstions
        self.displayPuckScanCompleteMessage = displayPuckScanCompleteMessage
        self.displayScanTimeoutMessage = displayScanTimeoutMessage
        self.is_latest_holder_barcode = is_latest_holder_barcode
        self.startCountdown = startCountdown
        self.addRecordFrame = addRecordFrame
        self.clear_frame = clear_frame 
        self.scanCompleted = scanCompleted

        
    #@pyqtSlot(Frame, Frame)
    def start_processor(self, side_frame, top_frame):    
        if not self.top_processor_thread.isRunning():
                self.processor_worker = SideProcessor(self._manager.side_camera_stream, side_frame)
                self.processor_worker.moveToThread(self.side_processor_thread)
                self.side_processor_thread.started.connect(self.processor_worker.run)
                self.processor_worker.finished.connect(self.side_processor_thread.quit)
                self.processor_worker.finished.connect(self.processor_worker.deleteLater) 
                self.processor_worker.finished.connect(self.side_processor_thread.wait)
                self.side_processor_thread.start()
                #self.processor_worker.side_scan_error_signal.connect(self.clear_frame_display_message)
                self.processor_worker.side_result_signal.connect(self.set_new_side_result)
                self.processor_worker.finished.connect(lambda: self.process_side(top_frame))
                
              
    def process_side(self, top_frame):
        if self.processing_flag:
            if not self.timer.isActive():
                self.timer.start(self._duration*1000) # convert duration to miliseconds
                self.startCountdown(self._duration) #UI
                self.clear_frame() #UI  
            self.top_processor_worker = TopProcessor(self._manager.top_camera_stream, top_frame)
            self.top_processor_worker.moveToThread(self.top_processor_thread)
            self.top_processor_thread.started.connect(self.top_processor_worker.run)
            self.top_processor_worker.finished.connect(self.top_processor_thread.quit)
            self.top_processor_worker.finished.connect(self.top_processor_thread.wait)
            self.top_processor_worker.finished.connect(self.top_processor_worker.deleteLater) 
            self.top_processor_thread.start()
            self.top_processor_worker.full_and_valid_signal.connect(self.set_full_and_valid_scan)
            self.top_processor_worker.top_result_signal.connect(self.set_new_top_result)
            
    def _on_time_out(self):
        self.processing_flag = False
        result_first_barcode = self._side_result.get_first_barcode().data()
        if self.is_latest_holder_barcode(result_first_barcode): #scan successfully added to the table
            self.displayPuckScanCompleteMessage() 
        else:
            self.displayScanTimeoutMessage() 

    @pyqtSlot(ScanResult)
    def set_new_side_result(self, result): 
        self._side_result = result 
        self._set_top_porcessing_flag()
        
    @pyqtSlot(ScanResult)
    def set_new_top_result(self, result): 
        self._top_result = result 
        self.addRecordFrame(self._top_result, self._side_result) #UI
    
    def _set_top_porcessing_flag(self):
        result_first_barcode = self._side_result.get_first_barcode().data()
        if not self.is_latest_holder_barcode(result_first_barcode):
            self.processing_flag = True
        
    def set_full_and_valid_scan(self): #fast track time_out
        self.timer.stop()
        self.processing_flag = False
        self.displayPuckScanCompleteMessage()
        self.scanCompleted() #UI
