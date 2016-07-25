from __future__ import division

import math
import cv2
import numpy as np

from .finder_pattern import FinderPattern
from dls_barcode.util import Transform, Image, Color


class SquareLocator:
    """ Utility to locate a single datamatrix finder pattern in a small image in which the datamatrix
    is located roughly in the middle of the image, but at any orientation. """

    DEBUG = False

    OPT_ADAPT_SIZE = True

    # Specifies the geometry of the text that appears above and below each
    # barcode relative to barcode size.
    GAP = 0.1
    TXT_HEIGHT = 0.2
    TXT_WIDTH = 0.75
    TXT_OFFSET = 0.5 * (1 + TXT_HEIGHT) + GAP

    def __init__(self):
        self.metric_cache = dict()
        self.count = 0

    def locate(self, gray_img, barcode_size):
        """ Get the finder pattern of the datamatrix of the specified side length. """
        # Clear cache
        self.metric_cache = dict()
        self.count = 0

        if self.DEBUG:
            gray_img.rescale(4).popup()

        # Threshold the image converting it to a binary image
        binary_image = self._adaptive_threshold(gray_img.img, 99, 0)

        # Find the transform that best fits the square to the barcode
        best_transform = self._minimise_integer_grid(binary_image, gray_img.center(), barcode_size)

        # Get the finder pattern
        fp = self._locate_finder_in_square(binary_image, best_transform, barcode_size)

        if self.DEBUG and fp is not None:
            img = _draw_finder_pattern(binary_image, best_transform, fp)
            img.rescale(4).popup()

        best_transform = self._find_best_fp(binary_image, best_transform, barcode_size)
        fp = self._locate_finder_in_square(binary_image, best_transform, barcode_size)

        if self.DEBUG and fp is not None:
            img = _draw_finder_pattern(binary_image, best_transform, fp)
            img.rescale(4).popup()
            print(self.count)

        return fp

    @staticmethod
    def _adaptive_threshold(image, block_size, c):
        """ Perform an adaptive threshold operation on the image, reducing it to a binary image.
        """
        thresh = cv2.adaptiveThreshold(image, 255.0,
                                       cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c)

        return Image(None, thresh)

    def _minimise_integer_grid(self, binary_image, center, side_length):
        """ Attempt to locate the square area (of the specified size, centered on the specified
        center point) in the binary image which has the minimum brightness.

        The datamatrix is a relatively dark area on a relative light background, so the area
        corresponding to the datamatrix should have the lowest brightness.
        """
        done = False

        initial_transform = Transform(int(center[0]), int(center[1]), 0, 1)
        best_val = 1000000000000000
        best_trs = initial_transform

        if self.DEBUG:
            img = binary_image.to_alpha()
            img = _draw_square(img, initial_transform, side_length)
            img.rescale(4).popup()

        count = 0
        done_previous = False
        while not done:
            count += 1
            transforms = self._make_minimisation_transforms(initial_transform, iteration=count)

            for trs in transforms:
                val = self._calculate_square_metric(binary_image, trs, side_length)
                if val < best_val:
                    best_val = val
                    best_trs = trs

            # if transform doesn't move for 2 iterations (one angle, one space), it
            # has reached a minimum
            if best_trs == initial_transform:
                if done_previous:
                    done = True
                done_previous = True
            else:
                done_previous = False

            initial_transform = best_trs

            if self.DEBUG:
                img = binary_image.to_alpha()
                img = _draw_square(img, initial_transform, side_length)
                img.rescale(4).popup()

        return best_trs

    @staticmethod
    def _make_minimisation_transforms(transform, iteration=0):
        """ Create a selection of transforms that differ slightly from the supplied transform.
        """
        angle_points = [0]
        grid_points = [0]

        even = iteration % 2 == 0

        if even:
            grid_points = [-5, -1, 0, 1, 5]
        else:
            angle_points = [-30, -20, -10, -5, -2, -1, 0, 1, 2, 5, 10, 20, 30]

        return SquareLocator._make_transforms(transform, grid_points, angle_points)

    @staticmethod
    def _make_fp_optimiser_transforms(transform):
        grid_points = range(-2, 3)
        angle_points = range(-2, 3)

        return SquareLocator._make_transforms(transform, grid_points, angle_points)

    @staticmethod
    def _make_transforms(transform, grid_points, angle_points):
        transforms = []

        for x in grid_points:
            for y in grid_points:
                for degrees in angle_points:
                    radians = degrees * math.pi / 180
                    trs = transform.by_offset(x, y)
                    trs = trs.by_rotation(radians)
                    transforms.append(trs)

        return transforms

    def _calculate_square_metric(self, binary_image, transform, size):
        """ For the square area (defined by the transform and size) in the binary
        image, calculate the average brightness per pixel.

        The datamatrix is a relatively dark area on a relative light background,
        so a lower average brightness corresponds to a greater likelihood of the
        area being the datamatrix.
        """
        cx, cy = transform.x, transform.y
        center = (cx, cy)
        angle = transform.rot

        # Create cache key
        key = (angle, center)

        # If this x,y,angle combination has been seen before, retrieve the previous cached result
        if key in self.metric_cache:
            brightness = self.metric_cache[key]

        else:
            rotated = binary_image.rotate(angle, center)
            brightness = rotated.calculate_brightness(center, size, size)

            # Store in dictionary
            self.metric_cache[key] = brightness
            self.count += 1

        return brightness

    def _calculate_square_and_writing_metric(self, binary_image, transform, size):
        """ Similar to the _calculate_square_metric function above, but also includes the regions above
        and below that barcode that contain a text version of the information contained in the barcode.
        This may do a better job of correctly fitting the square in certain circumstances, but may also
        get trapped if there are dark/shadow regions around the edge of the image. """
        cx, cy = transform.x, transform.y
        center = (cx, cy)
        angle = transform.rot

        rotated = binary_image.rotate(angle, center)
        brightness = rotated.calculate_brightness(center, size, size) * size**2

        txt_height = self.TXT_HEIGHT * size
        txt_width = self.TXT_WIDTH * size
        area = txt_width * txt_height

        rect1_center = (cx, cy + self.TXT_OFFSET*size)
        rect2_center = (cx, cy - self.TXT_OFFSET*size)

        brightness += rotated.calculate_brightness(rect1_center, txt_width, txt_height) * area
        brightness += rotated.calculate_brightness(rect2_center, txt_width, txt_height) * area

        brightness /= (size**2 + 2*area)

        self.count += 1
        return brightness

    def _find_best_fp(self, binary_image, initial_transform, side_length):
        best_val = 1000000000000000
        best_trs = initial_transform

        kings = self._make_fp_optimiser_transforms(initial_transform)
        for trs in kings:
            val = self._calculate_fp_metric(binary_image, trs, side_length)
            if val < best_val:
                best_val = val
                best_trs = trs

        return best_trs

    def _calculate_fp_metric(self, image, transform, size):
        """ For the located barcode in the image, identify which of the sides make
        up the finder pattern.
        """
        self.count += 1
        radius = int(round(size/2))
        cx, cy = transform.x, transform.y
        angle = transform.rot

        rotated = image.rotate(angle, (cx, cy))

        sx1, sy1 = cx-radius, cy-radius
        sx2, sy2 = cx+radius, cy+radius
        thick = int(round(size / 14))

        # Top
        x1, y1 = sx1, sy1
        x2, y2 = sx2, sy1 + thick
        top = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Left
        x1, y1 = sx1, sy1
        x2, y2 = sx1 + thick, sy2
        left = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Bottom
        x1, y1 = sx1, sy2 - thick
        x2, y2 = sx2, sy2
        bottom = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Right
        x1, y1 = sx2 - thick, sy1
        x2, y2 = sx2, sy2
        right = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Identify finder edges
        if top < bottom and left < right:
            val = top + left
        elif top < bottom and right < left:
            val = top + right
        elif bottom < top and left < right:
            val = bottom + left
        elif bottom < top and right < left:
            val = bottom + right
        else:
            val = 100000000

        return val

    @staticmethod
    def _locate_finder_in_square(image, transform, size):
        """ For the located barcode in the image, identify which of the sides make
        up the finder pattern.
        """
        radius = int(round(size/2))
        cx, cy = transform.x, transform.y
        angle = transform.rot

        rotated = image.rotate(angle, (cx, cy))

        sx1, sy1 = cx-radius, cy-radius
        sx2, sy2 = cx+radius, cy+radius
        thick = int(round(size / 14))

        # Top
        x1, y1 = sx1, sy1
        x2, y2 = sx2, sy1 + thick
        top = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Left
        x1, y1 = sx1, sy1
        x2, y2 = sx1 + thick, sy2
        left = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Bottom
        x1, y1 = sx1, sy2 - thick
        x2, y2 = sx2, sy2
        bottom = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Right
        x1, y1 = sx2 - thick, sy1
        x2, y2 = sx2, sy2
        right = np.sum(rotated.img[y1:y2, x1:x2]) / (size * thick)

        # Identify finder edges
        if top < bottom and left < right:
            c1 = [sx1, sy1]
            c2 = [sx1, sy2]
            c3 = [sx2, sy1]
        elif top < bottom and right < left:
            c1 = [sx2, sy1]
            c2 = [sx1, sy1]
            c3 = [sx2, sy2]
        elif bottom < top and left < right:
            c1 = [sx1, sy2]
            c2 = [sx2, sy2]
            c3 = [sx1, sy1]
        elif bottom < top and right < left:
            c1 = [sx2, sy2]
            c2 = [sx2, sy1]
            c3 = [sx1, sy2]
        else:
            return None

        # rotate points around center of square
        center = (cx, cy)
        c1 = _rotate_around_point(c1, angle, center)
        c2 = _rotate_around_point(c2, angle, center)
        c3 = _rotate_around_point(c3, angle, center)

        # Create finder pattern
        c1 = (int(c1[0]), int(c1[1]))
        side1 = (int(c2[0]-c1[0]), int(c2[1]-c1[1]))
        side2 = (int(c3[0]-c1[0]), int(c3[1]-c1[1]))
        fp = FinderPattern(c1, side1, side2)

        return fp


def _rotate_around_point(point, angle, center):
    """ Rotate the point about the center position """
    x = point[0] - center[0]
    y = point[1] - center[1]
    cos = math.cos(angle)
    sin = math.sin(angle)
    x_ = x * cos - y * sin
    y_ = x * sin + y * cos
    return x_+center[0], y_+center[1]


def _draw_square(image, transform, size):
    radius = size/2
    center = (transform.x, transform.y)
    rotated = image.rotate(transform.rot, center)

    x1, y1 = center[0]-radius, center[1]-radius
    x2, y2 = x1 + size, y1 + size

    roi = (x1, y1, x2, y2)
    marked_img = rotated.to_alpha()
    marked_img.draw_rectangle(roi, Color.Green(), 1)

    return marked_img


def _draw_square_and_writing(image, transform, size):
    marked_img = _draw_square(image, transform, size)

    txt_height = SquareLocator.TXT_HEIGHT * size
    txt_width = SquareLocator.TXT_WIDTH * size

    center = (transform.x, transform.y)
    x1 = center[0]-txt_width/2
    x2 = x1 + txt_width
    y_offset = SquareLocator.TXT_OFFSET*size

    y1 = center[1] + y_offset - txt_height/2
    y2 = y1 + txt_height
    marked_img.draw_rectangle((x1, y1, x2, y2), Color.Green(), 1)

    y1 = center[1] - y_offset - txt_height/2
    y2 = y1 + txt_height
    marked_img.draw_rectangle((x1, y1, x2, y2), Color.Green(), 1)

    return marked_img


def _draw_finder_pattern(image, transform, fp):
    center = (transform.x, transform.y)
    angle = transform.rot
    rotated = image.rotate(transform.rot, center)

    c1 = _rotate_around_point(fp.c1, -angle, center)
    c2 = _rotate_around_point(fp.c2, -angle, center)
    c3 = _rotate_around_point(fp.c3, -angle, center)

    img = rotated.to_alpha()
    img.draw_line(c1, c2, Color.Green(), 1)
    img.draw_line(c1, c3, Color.Green(), 1)

    return img
