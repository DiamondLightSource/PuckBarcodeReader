from PyQt5.QtCore import QObject, pyqtSignal
from dls_barcode.camera.scanner_message import ScanErrorMessage
from dls_barcode.scan.scan_result import ScanResult


class Processor(QObject):
    finished = pyqtSignal()
    side_result_signal = pyqtSignal(ScanResult)
    side_top_result_signal = pyqtSignal(ScanResult, ScanResult)
    side_scan_error_signal = pyqtSignal(ScanErrorMessage)
    successfull_scan_signal = pyqtSignal()
    full_and_valid_signal = pyqtSignal()
    
    def __init__(self, side_camera_stream, top_camera_stream, side_frame, top_frame) -> None:
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        self._top_frame= top_frame
        self._side_frame = side_frame 

    def run(self):
        side_result = self._side_camera_stream.process_frame(self._side_frame)
        if side_result.error() is not None:
            self.side_scan_error_signal.emit(side_result.error())
        if side_result.has_valid_barcodes():
            self.side_result_signal.emit(side_result)
        
        top_result = self._top_camera_stream.process_frame(self._top_frame)    
                 
        if  side_result.has_valid_barcodes() and top_result.success():
            self.side_top_result_signal.emit(side_result,top_result)
            self.successfull_scan_signal.emit()
            if top_result.is_full_valid():
                self.full_and_valid_signal.emit()
                
        self.finished.emit()



