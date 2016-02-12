import cv2
import math
import numpy as np

class CvImage:
    """Class that wraps an OpenCV image and can perform various
    operations on it that are useful in this program.
    """
    WHITE = (255,255,255,255)
    BLACK = (0,0,0,255)

    BLUE = (255,0,0,255)
    RED = (0,0,255,255)
    GREEN = (0,255,0,255)

    YELLOW = (0,255,255,255)
    CYAN = (255,255,0,255)
    MAGENTA = (255,0,255,255)

    ORANGE = (0,128,255,255)
    PURPLE = (255,0,128,255)

    def __init__(self, filename, img=None):
        if filename is not None:
            self.img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        else:
            self.img = img

        size = self.img.shape
        self.width = size[1]
        self.height = size[0]

        if len(size) > 2:
            self.channels = size[2]
        else:
            self.channels = 1

        # All draw requests will be offset by this amount
        self.draw_offset = (0,0)

    def save_as(self, filename):
        """ Write an OpenCV image to file """
        cv2.imwrite(filename, self.img)

    def popup(self):
        """Pop up a window to display an image until a key is pressed (blocking)."""
        cv2.imshow('dbg', self.img)
        cv2.waitKey(0)

    def center(self):
        """ Return the center point of the image. """
        return (self.width/2, self.height/2)

    def rescale(self, factor):
        """ Return a new Image that is a version of this image, resized to the specified scale
        """
        scaled_size = (int(self.width * factor), int(self.height * factor))
        return self.resize(scaled_size)

    def resize(self, new_size):
        """ Return a new Image that is a resized version of this one
        """
        resized_img = cv2.resize(self.img, new_size)
        return CvImage(None, resized_img)

    def rotate(self, angle, center):
        """ Rotate the image around the specified center. Note that this will
        cut off any areas that are rotated out of the frame.
        """
        degrees = angle * 180 / math.pi
        matrix = cv2.getRotationMatrix2D(center, degrees, 1.0)

        rotated = cv2.warpAffine(self.img, matrix, (self.width, self.height))
        return CvImage(None, rotated)

    def to_alpha(self):
        """Convert the image into a 4 channel BGRA image
        """
        if self.channels != 4:
            alpha = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
            return CvImage(filename=None, img=alpha)
        else:
            return CvImage(filename=None, img=self.img)

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

    def draw_rectangle(self, roi, color, thickness=2):
        """ Draw the specified rectangle on the image (in place) """
        top_left = self._format_point((roi[0], roi[1]))
        bottom_right = self._format_point((roi[2], roi[3]))
        cv2.rectangle(self.img, top_left, bottom_right, color, thickness=thickness)

    def draw_circle(self, center, radius, color, thickness=2):
        """ Draw the specified circle on the image (in place) """
        center = self._format_point(center)
        cv2.circle(self.img, center, int(radius), color, thickness=thickness)

    def draw_dot(self, center, color, thickness=5):
        """ Draw the specified dot on the image (in place) """
        center = self._format_point(center)
        cv2.circle(self.img, tuple(center), radius=0, color=color, thickness=thickness)

    def draw_line(self, p1, p2, color, thickness=2):
        """ Draw the specified line on the image (in place) """
        p1 = self._format_point(p1)
        p2 = self._format_point(p2)
        cv2.line(self.img, p1, p2, color, thickness=thickness)

    def draw_text(self, text, position, color, centered=False, scale=1.5, thickness=3):
        """ Draw the specified text on the image (in place) """
        if centered:
            textsize = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale, thickness=thickness)[0]
            position = (int(position[0]-textsize[0]/2), int(position[1]+textsize[1]/2))
        position = self._format_point(position)
        cv2.putText(self.img, text, position, cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale, color=color, thickness=thickness)

    def _format_point(self, point):
        """ Offset the point and ensure the coordinates are integers
        """
        return (int(point[0]+self.draw_offset[0]), int(point[1]+self.draw_offset[1]))


    @staticmethod
    def blank(width, height, channels=3, value=0):
        """ Return a new empty image of the specified size.
        """
        blank_image = np.full((height, width, channels), value, np.uint8)
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


