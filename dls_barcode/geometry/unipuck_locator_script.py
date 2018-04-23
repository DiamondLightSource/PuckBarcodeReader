import cv2
import numpy as np
import math

from dls_barcode.geometry.unipuck import Unipuck
from dls_util import Image, Color
from dls_util.shape import Point

OPENCV_MAJOR = cv2.__version__[0]

class UnipuckLocatorScript:
    """ Utility for finding the positions of all of the datamatrix barcodes
    in an image """

    def __init__(self, image):
        self.image = image.img

    def locate_characteristic_points(self):
        self.puck_contour()

    def puck_contour(self):

        blurred = cv2.GaussianBlur(self.image, (9, 9), 0)
        edged = cv2.adaptiveThreshold(blurred, 255.0, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 35, 16)
        self.popup_image(blurred, 'bl')
        self.popup_image(edged, 'ero')

        _ ,contours, _ = cv2.findContours(255 - edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)


        c = cnts[0]

        #peri = cv2.arcLength(c, True)
        #approx = cv2.approxPolyDP(c, 2, True)

        #cv2.drawContours(self.image, [approx], -1, (255, 255, 255), 2)
        #self.popup_image(self.image, 'cn1')

        blank_image = np.zeros(self.image.shape, np.uint8)

        (x, y), radius = cv2.minEnclosingCircle(c)

        cv2.circle(blank_image, (int(x), int(y)), int(radius), (255, 255, 255), -1)
        self.popup_image(self.image, 'cn1')

        cv2.drawContours(blank_image, [c] , -1, (0, 0, 0), -1)
        self.popup_image(blank_image, 'cn2')

        morph2 = self._do_open_morph(blank_image, 8)

        self.popup_image(morph2, 'morph2')
        im, contours_m, hierarchy = cv2.findContours(morph2, 2, 1)

        tr = cv2.imread('/Users/uneuman/PycharmProjects/PuckBarcodeReader/tests/test-resources/blue_stand/fit.png', 0)

        self.popup_image(tr, 'fit')

        im,contours, hierarchy = cv2.findContours(255-tr, 2, 1)

        cnt_tr = contours[0]
        # cv2.drawContours(self.image, cnt_tr, -1, (255, 255, 255), 2)
        ret_min = 1000000
        cnt_min = None
        for cnt_m in contours_m:
            ret = cv2.matchShapes(cnt_tr, cnt_m, 1, 0.0)
            if ret < ret_min:
                ret_min = ret
                cnt_min = cnt_m

        cv2.drawContours(self.image, cnt_min, -1, (255, 255, 255), 5)
        self.popup_image(self.image, 'cnt1')

        M = cv2.moments(cnt_min)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        Image(self.image).draw_dot(Point(cx, cy), Color.White())
        self.popup_image(self.image, 'cnt1')

        rad = math.atan2(cy - y, cx - x)
        deg = math.degrees(rad) #location of the feature

        deg_pck = deg - 90
        rad_pck = rad - math.pi/2

        #test

        uni = Unipuck(Point(x, y), radius, rad_pck)#takes degrees
        uni.calculate_slot_bounds(uni.center(),uni.radius(), uni.angle())
        uni.draw_plate(Image(self.image), Color.White())
        self.popup_image(self.image, 'test')




    def popup_image(self, ima, name):
        cv2.namedWindow(name, flags=cv2.WINDOW_NORMAL)
        cv2.imshow(name, ima)
        cv2.waitKey(0)
        #cv2.destroyAllWindows()

    def _get_contours(self, edged):
        if OPENCV_MAJOR == '3':
            _, raw_contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        else:
            raw_contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        return raw_contours

    @staticmethod
    def _do_dilate_morph(threshold_image, morph_size):
        """ Perform a generic morphological operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(threshold_image, cv2.MORPH_DILATE, element, iterations=1)
        return closed

    @staticmethod
    def _do_erode_morph(threshold_image, morph_size):
        """ Perform a generic morphological operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(threshold_image, cv2.MORPH_ERODE, element, iterations=1)
        return closed

    @staticmethod
    def _do_close_morph(threshold_image, morph_size):
        """ Perform a generic morphological operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(threshold_image, cv2.MORPH_CLOSE, element, iterations=1)
        return closed

    @staticmethod
    def _do_open_morph(threshold_image, morph_size):
        """ Perform a generic morphological operation on an image. """
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_size, morph_size))
        closed = cv2.morphologyEx(threshold_image, cv2.MORPH_OPEN, element, iterations=1)
        return closed