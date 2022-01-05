from PyQt5.QtCore import  QObject, pyqtSignal

from dls_util.cv.frame import Frame

class FrameGrabber(QObject):
    finished = pyqtSignal()
    new_side_frame = pyqtSignal(Frame)
    new_top_frame = pyqtSignal(Frame)
    images_collected = pyqtSignal(Frame, Frame)
    camera_error = pyqtSignal()

    
    def __init__(self, side_camera_stream, top_camera_stream):
        super().__init__()
        self._side_camera_stream = side_camera_stream
        self._top_camera_stream = top_camera_stream
        # run flag is used to stop the main scan loop in a clean way
        self._run_flag = True


    def run(self): 
        while self._run_flag: 
            side_frame = self._side_camera_stream.get_frame()
            if side_frame is not None:
                self.new_side_frame.emit(side_frame)
            else:
                self.camera_error.emit()
                break
            top_frame = self._top_camera_stream.get_frame()
            if top_frame is not None:
                self.new_top_frame.emit(top_frame)
            else:
                self.camera_error.emit()
                break
            if top_frame is not None and side_frame is not None: 
                self.images_collected.emit(side_frame, top_frame)
                                    
        self.finished.emit()

    def stop(self):
        self._run_flag = False
        
