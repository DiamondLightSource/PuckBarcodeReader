import cv2 as opencv

_OPENCV_MAJOR = opencv.__version__[0]
DEFAULT_CAMERA_NUMBER = 0

class CameraManager:

    def __init__(self, camera):
        self._camera = camera
        self._cap = None

    def create_capture(self):
        self._cap = opencv.VideoCapture(self._camera.get_camera_number())
        self._set_width(self._camera.get_camera_width())
        self._set_height(self._camera.get_camera_height())

    def get_frame(self):
        read_ok, frame = self._cap.read()
        if read_ok:
            return frame
        else:
            raise IOError

    def release_resources(self):
        if self._cap is not None:
            self._cap.release()

    def get_width(self):
        return self._cap.get(self._get_width_flag())

    def get_height(self):
        return self._cap.get(self._get_height_flag())

    def _set_width(self, width):
        self._cap.set(self._get_width_flag(), width)

    def _set_height(self, height):
        self._cap.set(self._get_height_flag(), height)

    def _get_width_flag(self):
        if _OPENCV_MAJOR == '2':
            return opencv.cv.CV_CAP_PROP_FRAME_COUNT
        else:
            return opencv.CAP_PROP_FRAME_WIDTH

    def _get_height_flag(self):
        if _OPENCV_MAJOR == '2':
            return opencv.cv.CV_CAP_PROP_FRAME_COUNT
        else:
            return opencv.CAP_PROP_FRAME_HEIGHT

    @staticmethod
    def open_camera_controls(camera_num):
        """Open the camera's settings panel.
         This sometimes crashes but it's out of our control and the CAP_PROP_SETTINGS is not documented"""
        cap = opencv.VideoCapture(camera_num)
        cap.set(opencv.CAP_PROP_SETTINGS, 1)
