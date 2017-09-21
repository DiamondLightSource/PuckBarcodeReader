import cv2 as opencv

_OPENCV_MAJOR = opencv.__version__[0]
DEFAULT_CAMERA_NUMBER = 0


class CameraStream:
    """ Class that wraps an OpenCV VideoCapture
    """
    def __init__(self, camera_number, width, height):
        self._camera_number = camera_number
        self._cap = self._create_capture()
        self.set_width(width)
        self.set_height(height)

    def get_frame(self):
        read_ok, frame = self._cap.read()
        # print("--- Read OK: " + str(read_ok))
        return frame

    def release_resources(self):
        self._cap.release()

    def set_camera_number(self, camera_number):
        if camera_number == self._camera_number:
            return

        width = self.get_width()
        height = self.get_height()
        self.release_resources()
        self._cap = self._create_capture()
        self.set_width(width)
        self.set_height(height)

    def set_width(self, width):
        self._cap.set(self._get_width_flag(), width)

    def set_height(self, height):
        self._cap.set(self._get_height_flag(), height)

    def get_width(self):
        return self._cap.get(self._get_width_flag())

    def get_height(self):
        return self._cap.get(self._get_height_flag())

    def _create_capture(self):
        cap = opencv.VideoCapture(self._camera_number)
        read_ok, _ = cap.read()
        if not read_ok:
            print("Read on " + str(self._camera_number) + " failed. Using default index")
            self._camera_number = DEFAULT_CAMERA_NUMBER
            cap = opencv.VideoCapture(self._camera_number)

        return cap

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


