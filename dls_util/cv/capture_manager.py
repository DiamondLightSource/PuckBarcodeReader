import cv2 as opencv

_OPENCV_MAJOR = opencv.__version__[0]
DEFAULT_CAMERA_NUMBER = 0


def _get_height_flag():
    if _OPENCV_MAJOR == '2':
        return opencv.cv.CV_CAP_PROP_FRAME_COUNT
    else:
        return opencv.CAP_PROP_FRAME_HEIGHT


def _get_width_flag():
    if _OPENCV_MAJOR == '2':
        return opencv.cv.CV_CAP_PROP_FRAME_COUNT
    else:
        return opencv.CAP_PROP_FRAME_WIDTH


#def get_available_resolutions():
#    return [(640,480), (800,600), (1600,1200), (2048, 1536), (2592,1944)]


class CaptureManager:

    def __init__(self, camera):
        self._camera = camera
        self._cap = None
        self._frame = None
        self._read_ok = False

    def create_capture(self):
        self._cap = opencv.VideoCapture(self._camera.get_number(),opencv.CAP_DSHOW)
        self._set_width(self._camera.get_width())
        self._set_height(self._camera.get_height())

    def get_frame(self):
        return self._frame

    def is_read_ok(self):
        return self._read_ok

    def read_frame(self):
        self._read_ok, self._frame = self._cap.read()

    def release_resources(self):
        if self._cap is not None:
            self._cap.release()

    #def get_width(self):
    #    return self._cap.get(_get_width_flag())

    #def get_height(self):
    #    return self._cap.get(_get_height_flag())

    def _set_width(self, width):
        # opencv adjusts the setting to the camera specification
        self._cap.set(_get_width_flag(), width)
        print(self._cap.get(_get_width_flag()))

    def _set_height(self, height):
        self._cap.set(_get_height_flag(), height)

    @staticmethod
    def open_camera_controls(camera_num):
        """Open the camera's settings panel.
         This sometimes crashes but it's out of our control and the CAP_PROP_SETTINGS is not documented"""
        cap = opencv.VideoCapture(camera_num)
        cap.set(opencv.CAP_PROP_SETTINGS, 1)