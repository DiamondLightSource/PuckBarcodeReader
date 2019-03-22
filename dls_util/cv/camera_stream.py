import logging

import cv2 as opencv

_OPENCV_MAJOR = opencv.__version__[0]
DEFAULT_CAMERA_NUMBER = 0


class CameraStream:
    """ Class that wraps an OpenCV VideoCapture
    """
    def __init__(self, camera_number, width, height, use_default_as_backup=True):
        self._cap = self._create_capture(camera_number, use_default_as_backup)
        self._set_width(width)
        self._set_height(height)

    def get_frame(self):
        read_ok, frame = self._cap.read()
        return frame

    def release_resources(self):
        self._cap.release()

    def get_width(self):
        return self._cap.get(self._get_width_flag())

    def get_height(self):
        return self._cap.get(self._get_height_flag())

    def _set_width(self, width):
        self._cap.set(self._get_width_flag(), width)

    def _set_height(self, height):
        self._cap.set(self._get_height_flag(), height)

    def _create_capture(self, camera_number, use_default_as_backup):
        cap = opencv.VideoCapture(camera_number)
        read_ok, _ = cap.read()
        if not read_ok:
            if use_default_as_backup:
                print("Read on " + str(camera_number) + " failed. Using default index")
                cap = opencv.VideoCapture(DEFAULT_CAMERA_NUMBER)
            else:
                raise IOError

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

    @staticmethod
    def open_camera_controls(camera_num):
        """Open the camera's settings panel.
         This sometimes crashes but it's out of our control and the CAP_PROP_SETTINGS is not documented"""
        cap = opencv.VideoCapture(camera_num)
        cap.set(opencv.CAP_PROP_SETTINGS, 1)


