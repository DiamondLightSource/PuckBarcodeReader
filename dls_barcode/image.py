from pkg_resources import require;  require('numpy')
import cv2
import numpy as np

class CvImage:
    """Class that wraps an OpenCV image and can perform various
    operations on it that are useful in this program.
    """
    WHITE = (255,255,255)
    BLACK = (0,0,0)

    BLUE = (255,0,0)
    RED = (0,0,255)
    GREEN = (0,255,0)

    YELLOW = (0,255,255)
    CYAN = (255,255,0)
    MAGENTA = (255,0,255)

    ORANGE = (0,128,255)
    PURPLE = (255,0,128)

    def __init__(self, filename, img=None):
        if filename is not None:
            self.img = cv2.imread(filename)
        else:
            self.img = img

    def save_as(self, filename):
        """ Write an OpenCV image to file """
        cv2.imwrite(filename, self.img)

    def popup(self):
        """Pop up a window to display an image until a key is pressed (blocking)."""
        cv2.imshow('dbg', self.img)
        cv2.waitKey(0)

    def center(self):
        height, width = self.img.shape[:2]
        return (width/2, height/2)

    def draw_rectangle(self, roi, color, thickness=2):
        top_left = tuple([roi[0], roi[1]])
        bottom_right = tuple([roi[2], roi[3]])
        cv2.rectangle(self.img, top_left, bottom_right, color, thickness=thickness)

    def draw_circle(self, center, radius, color, thickness=2):
        cv2.circle(self.img, tuple(center), int(radius), color, thickness=thickness)

    def draw_dot(self, center, color, thickness=5):
        cv2.circle(self.img, tuple(center), radius=0, color=color, thickness=thickness)

    def draw_line(self, p1, p2, color, thickness=2):
        cv2.line(self.img, p1, p2, color, thickness=thickness)

    def draw_text(self, text, position, color, centered=False, scale=1.5, thickness=3):
        if centered:
            textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale, thickness=thickness)[0]
            position = (int(position[0]-textsize[0]/2), int(position[1]+textsize[1]/2))
        cv2.putText(self.img, text, position, cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale, color=color, thickness=thickness)

    def to_grayscale(self):
        """Convert the image to a grey image.
        """
        if len(self.img.shape) in (3, 4):
            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            return CvImage(filename=None, img=gray)
        else:
            assert len(self.img.shape) == 2
            return CvImage(filename=None, img=self.img)

    def crop_image(self, center, radius):
        self.img, _ = CvImage.sub_image(self.img, center, radius)

    @staticmethod
    def blank(width, height):
        blank_image = np.zeros((height,width,3), np.uint8)
        return CvImage(filename=None, img=blank_image)

    @staticmethod
    def sub_image(img, center, radius):
        """ Returns a new (raw) OpenCV image that is a section of the existing image.
        The section is square with side length = 2*radius, and centered around the
        enter point
        """
        width = img.shape[1]
        height = img.shape[0]
        xstart = int(max(center[0] - radius, 0))
        xend = int(min(center[0] + radius, width))
        ystart = int(max(center[1] - radius, 0))
        yend = int(min(center[1] + radius, height))
        roi_rect = [xstart, ystart, xend, yend]
        return img[ystart:yend, xstart:xend], roi_rect

    @staticmethod
    def find_circle(img, minradius, maxradius):
        circle = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, dp=1.2,
            minDist=10000000, minRadius=int(minradius), maxRadius=int(maxradius))

        if circle is not None:
            circle = circle[0][0]
            center = [int(circle[0]), int(circle[1])]
            radius = int(circle[2])
            return [center, radius]
        else:
            return None


