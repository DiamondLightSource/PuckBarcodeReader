import cv2
import math
import numpy as np

from PyQt4 import QtCore
from PyQt4.QtGui import QImage, QPixmap

from util.shape import Point


class Image:
    """ Class that wraps an OpenCV image and can perform various useful operations on it.
    """
    def __init__(self, img):
        self.img = img

        size = self.img.shape
        self.width = size[1]
        self.height = size[0]

        if len(size) > 2:
            self.channels = size[2]
        else:
            self.channels = 1

        # All draw requests will be offset by this amount
        self.draw_offset = Point(0, 0)

    @staticmethod
    def from_file(filename):
        """ Return a new image by loading from the specified image file. """
        img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
        return Image(img)

    @staticmethod
    def blank(width, height, channels=3, value=0):
        """ Return a new empty image of the specified size. """
        blank_image = np.full((height, width, channels), value, np.uint8)
        return Image(img=blank_image)

    def save_as(self, filename):
        """ Write the image to the specified file. """
        cv2.imwrite(filename, self.img)

    def popup(self):
        """Pop up a window to display an image until a key is pressed (blocking)."""
        cv2.imshow('dbg', self.img)
        cv2.waitKey(0)

    def copy(self):
        """ Return an Image object which is a deep copy of this one. """
        return Image(self.img.copy())

    def center(self):
        """ Return the center point of the image. """
        return Point(self.width/2, self.height/2)

    ############################
    # Transformation Functions
    ############################
    def rescale(self, factor):
        """ Return a new Image that is a version of this image, resized to the specified scale
        """
        scaled_size = (int(self.width * factor), int(self.height * factor))
        return self.resize(scaled_size)

    def resize(self, new_size):
        """ Return a new Image that is a resized version of this one
        """
        resized_img = cv2.resize(self.img, new_size)
        return Image(resized_img)

    def rotate(self, radians, center):
        """ Rotate the image around the specified center. Note that this will
        cut off any areas that are rotated out of the frame.
        """
        degrees = radians * 180 / math.pi
        matrix = cv2.getRotationMatrix2D(center.tuple(), degrees, 1.0)

        rotated = cv2.warpAffine(self.img, matrix, (self.width, self.height))
        return Image(rotated)

    def rotate_no_clip(self, angle):
        """Rotate the image about its center point, but expand the frame of the image
        so that the whole rotated shape will be visible without any being cropped.
        """
        # Calculate the size the expanded image needs to be to contain rotated image
        x, y = self.width, self.height
        w = abs(x*math.cos(angle)) + abs(y*math.sin(angle))
        h = abs(x*math.sin(angle)) + abs(y*math.cos(angle))

        # Paste the image into a larger frame and rotate
        img = Image.blank(w, h, 4, 0)
        img.paste(self, w/2-x/2, h/2-y/2)
        rotated = img.rotate(angle, (w/2, h/2))

        return rotated

    def crop_image(self, center, radius):
        cropped, _ = self.sub_image(center, radius)
        self.img = cropped.img
        size = self.img.shape
        self.width = size[1]
        self.height = size[0]

    def crop_image_to_rectangle(self, rect):
        sub = self.img[rect[1]:rect[3], rect[0]:rect[2]]
        print(rect)
        self.img = sub
        size = self.img.shape
        self.width = size[1]
        self.height = size[0]

    def paste(self, src, x_off, y_off):
        """ Paste the source image onto the target one at the specified position.
        If any of the source is outside the bounds of this image, it will be
        lost.
        """
        x_off, y_off = int(x_off), int(y_off)

        # Overlap rectangle in target image coordinates
        width, height = src.width, src.height
        x1 = max(x_off, 0)
        y1 = max(y_off, 0)
        x2 = min(x_off + width, self.width)
        y2 = min(y_off + height, self.height)

        # Paste location is totally outside image
        if x1 > x2 or y1 > y2:
            return

        # Overlap rectangle in source image coordinates
        sx1 = x1 - x_off
        sy1 = y1 - y_off
        sx2 = x2 - x_off
        sy2 = y2 - y_off

        # Perform paste
        target = self.img
        source = src.img
        alpha = 3

        if self.channels == 4 and src.channels == 4:
            # Use alpha blending
            for c in range(0, 3):
                target[y1:y2, x1:x2, c] = source[sy1:sy2, sx1:sx2, c] * (source[sy1:sy2, sx1:sx2, alpha] / 255.0) \
                                          + target[y1:y2, x1:x2, c] * (1.0 - source[sy1:sy2, sx1:sx2, alpha] / 255.0)

            target[y1:y2, x1:x2, alpha] = np.full((y2-y1, x2-x1), 255, np.uint8)

        else:
            # No alpha blending
            target[y1:y2, x1:x2] = src.img[sy1:sy2, sx1:sx2]

    def sub_image(self, center, radius):
        """ Returns a new (raw) OpenCV image that is a section of the existing image.
        The section is square with side length = 2*radius, and centered around the
        enter point
        """
        width = self.img.shape[1]
        height = self.img.shape[0]
        xstart = int(max(center.x - radius, 0))
        xend = int(min(center.x + radius, width))
        ystart = int(max(center.y - radius, 0))
        yend = int(min(center.y + radius, height))
        roi_rect = [xstart, ystart, xend, yend]

        sub = self.img[ystart:yend, xstart:xend]
        return Image(sub), roi_rect

    ############################
    # Colour Space Conversions
    ############################
    def to_grayscale(self):
        """Convert the image to a grey image.
        """
        if len(self.img.shape) in (3, 4):
            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            return Image(gray)
        else:
            assert len(self.img.shape) == 2
            return Image(self.img)

    def to_color(self):
        """Convert the image into a 3 channel BGR image.
        """
        if self.channels == 4:
            color = cv2.cvtColor(self.img, cv2.COLOR_BGRA2BGR)
            return Image(color)
        elif self.channels == 1:
            color = cv2.cvtColor(self.img, cv2.COLOR_GRAY2BGR)
            return Image(color)
        else:
            return Image(self.img)

    def to_alpha(self):
        """ Convert the image into a 4 channel BGRA image.
        """
        if self.channels == 3:
            alpha = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
            return Image(alpha)
        elif self.channels == 1:
            alpha = cv2.cvtColor(self.img, cv2.COLOR_GRAY2BGRA)
            return Image(alpha)
        else:
            return Image(self.img)

    def to_qt_pixmap(self, scale=None):
        """ Convert the image into a QT pixmap that can be displayed in QT GUI elements. """
        bytes_per_line = 3 * self.width
        img = self.to_color().img
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb.data, self.width, self.height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        if scale is not None:
            pixmap = pixmap.scaled(scale, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        return pixmap

    ############################
    # Drawing Functions
    ############################
    def draw_rectangle(self, roi, color, thickness=2):
        """ Draw the specified rectangle on the image (in place). """
        top_left = self._format_point(Point(roi[0], roi[1]))
        bottom_right = self._format_point(Point(roi[2], roi[3]))
        cv2.rectangle(self.img, top_left.tuple(), bottom_right.tuple(), color.bgra(), thickness=thickness)

    def draw_circle(self, circle, color, thickness=2):
        """ Draw the specified circle on the image (in place). """
        center = self._format_point(circle.center())
        cv2.circle(self.img, center.tuple(), int(circle.radius()), color.bgra(), thickness=thickness)

    def draw_dot(self, center, color, thickness=5):
        """ Draw the specified dot on the image (in place). """
        center = self._format_point(center)
        cv2.circle(self.img, center.tuple(), radius=0, color=color.bgra(), thickness=thickness)

    def draw_line(self, p1, p2, color, thickness=2):
        """ Draw the specified line on the image (in place). """
        p1 = self._format_point(p1)
        p2 = self._format_point(p2)
        cv2.line(self.img, p1.tuple(), p2.tuple(), color.bgra(), thickness=thickness)

    def draw_text(self, text, position, color, centered=False, scale=1.5, thickness=3):
        """ Draw the specified text on the image (in place). """
        if centered:
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale, thickness=thickness)[0]
            text_size = Point(-text_size[0]/2.0, text_size[1]/2.0)
            position = (position + text_size)
        position = self._format_point(position)
        cv2.putText(self.img, text, position.tuple(), cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale,
                    color=color.bgra(), thickness=thickness)

    def _format_point(self, point):
        """ Offset the point and ensure the coordinates are integers. """
        return (point + self.draw_offset).intify()

    ############################
    # Analysis Functions
    ############################
    def calculate_brightness(self, center, width, height):
        """Return the average brightness over a small region surrounding a point.
        """
        x1, y1 = int(round(center.x - width / 2)), int(round(center.y - height / 2))
        x2, y2 = int(round(x1 + width)), int(round(y1 + height))

        brightness = np.sum(self.img[y1:y2, x1:x2]) / (width * height)
        return brightness
