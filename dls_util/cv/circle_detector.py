import cv2

from dls_util.shape import Point, Circle

_HOUGH_METHOD = cv2.HOUGH_GRADIENT


class CircleDetector:
    """ Wraps the OpenCV function 'cv2.HoughCircles' which can detect circles in an image.
    See:
       http://docs.opencv.org/2.4/modules/imgproc/doc/feature_detection.html?highlight=houghcircles
    """
    def __init__(self):
        self._canny_thresh = 150
        self._accumulator_thresh = 100
        self._dp = 2
        self._min_dist = 100
        self._min_radius = 100
        self._max_radius = 150
        self._method = _HOUGH_METHOD

    def set_canny_threshold(self, value): self._canny_thresh = value

    def set_accumulator_threshold(self, value): self._accumulator_thresh = value

    def set_dp(self, value): self._dp = value

    def set_minimum_separation(self, value): self._min_dist = value

    def set_minimum_radius(self, value): self._min_radius = value

    def set_maximum_radius(self, value): self._max_radius = value

    def find_circles(self, mono_img):
        raw_circles = cv2.HoughCircles(image=mono_img.img, method=self._method, dp=self._dp,
                                       minDist=self._min_dist, param1=self._canny_thresh,
                                       param2=self._accumulator_thresh, minRadius=int(self._min_radius),
                                       maxRadius=int(self._max_radius))

        circles = self._sanitize_circles(raw_circles)
        return circles

    @staticmethod
    def _sanitize_circles(raw_circles):
        circles = []
        if raw_circles is not None:
            for raw in raw_circles[0]:
                center = Point(int(raw[0]), int(raw[1]))
                radius = int(raw[2])
                circles.append(Circle(center, radius))

        return circles
