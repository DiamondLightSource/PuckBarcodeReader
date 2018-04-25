import cv2
import numpy as np
import math
import os

from dls_util.image.contours_manager import ContoursManager
from dls_util.image.image_morphology import ImageMorphology
from dls_barcode.geometry.unipuck import Unipuck
from dls_util import Color, Image
from dls_util.shape import Point

OPENCV_MAJOR = cv2.__version__[0]
# factores's values found during tests
FEATURE_MATCH_FACTOR = 0.07  # the lowest the number the closer the match
FEATURE_HULL_MATCH_FACTOR = 0.96  # maximum value is 1, higher value better match
#PUCK_FEATURE_AREA_FACTOR_MIN = 0.05  # discard small elements


class UnipuckLocator:
    """ Class which uses image processing to determine puck center location, radius and orientation.
    The image of a puck is firstly processed to find the circle enclosing the puck and its radius.
    Next a feature - the round cut on the edge of a puck - is detected.
    The position of the puck is known once the position of the feature is found."""

    def __init__(self, image):
        self.image = image.img.copy()
        self.unipuck_contours = None

    def find_location(self):
        # find center, radius and location of the puck
        # use feature detection to identify the orientation of the puck
        self.unipuck_contours = self._find_puck_contours()
        (x, y), radius = self._find_enclosing_circle_of_largest_contour()
        features_cnt = self._find_contours_of_features(x, y, radius)
        match_factor, match_cnt = self._find_feature(features_cnt)

        uni = None

        if (match_factor < FEATURE_MATCH_FACTOR):  # take only the very good feature matches
            hull = cv2.convexHull(match_cnt)
            hull_area = cv2.contourArea(hull)
            feature_area = cv2.contourArea(match_cnt)
            puck_area = math.pi * math.sqrt(radius)
            area_factor = feature_area / hull_area
            #puck_area_factor = feature_area / puck_area
            if round(area_factor, 2) > FEATURE_HULL_MATCH_FACTOR:# and puck_area_factor > PUCK_FEATURE_AREA_FACTOR_MIN:
                # take the features which have only small convexity defects

                (cx, cy) = self._find_contour_momentum(match_cnt)
                #blank_image = np.zeros([1000, 1000, 3], np.uint8)
                #cv2.drawContours(blank_image, [match_cnt], -1, (255, 255, 255), -1)
                #cv2.drawContours(self.image, [hull], -1, (255, 255, 255), 5)
                #self.popup_image(255- blank_image, 'cnt1')
                #self.save_image('C:/Users/rqq82173/PycharmProjects/PuckBarcodeReader/test_' + str(cx) + '.png', 255-blank_image)

                feature_orientation = math.atan2(cy - y, cx - x) # feature orientation
                puck_orientation = feature_orientation - math.pi / 2  # puck orientation shifted -pi/2 rad from feature orientation
                uni = Unipuck(Point(x, y), radius)
                uni.set_rotation(puck_orientation)
                uni.set_feature_center(Point(cx, cy))
                uni.set_feature_boarder(match_cnt)

                #uni.calculate_slot_bounds(uni.center(), uni.radius(), uni.angle())
                #uni.draw_plate(Image(self.image), Color.White())
                #self.popup_image(self.image, 'test')

        return uni

    def _find_puck_contours(self):
        # find contours of the image which is initially blurred and thresholded
        blurred = cv2.GaussianBlur(self.image, (9, 9), 0)
        edged = cv2.adaptiveThreshold(blurred, 255.0, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 35, 16)
        cnt = ContoursManager(255 - edged)
        cnt.find_all()

        # self.popup_image(blurred, 'bl')
        # self.popup_image(edged, 'ero')

        return cnt

    def _find_enclosing_circle_of_largest_contour(self):
        (x, y), radius = cv2.minEnclosingCircle(self.unipuck_contours.get_lagerst())
        return (int(x), int(y)), int(radius)

    def _find_contours_of_features(self, x, y, rad):
        # find features on the edge of the puck
        blank_image = np.zeros(self.image.shape, np.uint8)
        cv2.circle(blank_image, (x, y), rad, (255, 255, 255), -1)

        self.unipuck_contours.draw_largest_cnt(blank_image, Color.Black(), -1)

        # self.popup_image(blank_image, 'cn2')

        img_open = ImageMorphology(blank_image).do_open_morph(8)  # removes some white artifacts
        img_open_cnt = ContoursManager(img_open)
        img_open_cnt.find_all()

        # self.popup_image(img_open, 'morph2')

        return img_open_cnt

    def _find_feature(self, features_cnt):  # do this better
        # compares the feature from the image with the features found on the edge of the puck
        dir_path = os.path.dirname(os.path.realpath(__file__))
        f_path = os.path.join(dir_path, '..', '..', 'resources', 'features', 'fit.png')
        img_feature_cnt = ContoursManager(255 - self._read_feature_image(f_path))
        img_feature_cnt.find_all()

        match_factor, match_cnt = features_cnt.match_shapes(img_feature_cnt.get_lagerst())

        return match_factor, match_cnt

    def _read_feature_image(self, f_path):
        if os.path.exists(f_path):
            return cv2.imread(f_path, 0)
        else:
            raise IOError(2, "Cannot find", f_path)

    @staticmethod
    def _find_contour_momentum(c):
        M = cv2.moments(c)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])
        return cx, cy

    def popup_image(self, ima, name):
        cv2.namedWindow(name, flags=cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, ima)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    #
    # def save_image(self, name, img):
    #     cv2.imwrite(name, img)
