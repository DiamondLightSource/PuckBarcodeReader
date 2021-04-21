import cv2


class ContoursManager:
    """
    Image contours manager class.
    """
    def __init__(self, image):
        self.image = image
        self.contours = []

    def find_all(self):
        self.contours, _ = cv2.findContours(self.image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    def get_lagerst(self):
        cnts = sorted(self.contours, key=cv2.contourArea, reverse=True)
        return cnts[0]

    def draw_all_contours_self(self, color, thickness):
        cv2.drawContours(self.image, self.contours, -1, color.rgb(), thickness)

    def draw_contour_self(self, cnt, color, thickness):
        cv2.drawContours(self.image, [cnt], -1, color.rgb(), thickness)

    def draw_all_contours(self, image, color, thickness):
        cv2.drawContours(image, self.contours, -1, color.rgb(), thickness)

    def draw_largest_cnt(self, img, color, thickness):  # negative thickness means filled
        cv2.drawContours(img, [self.get_lagerst()], - 1, color.rgb(), thickness)

    def match_shapes(self, contour_pattern):
        ret_min = 1000000
        cnt_min = None
        for cnt_m in self.contours:
            ret = cv2.matchShapes(contour_pattern, cnt_m, 1, 0.0)
            if ret < ret_min:
                ret_min = ret
                cnt_min = cnt_m
        return ret_min, cnt_min




