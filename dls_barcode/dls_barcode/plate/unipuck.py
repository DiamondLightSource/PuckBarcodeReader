from __future__ import division
import math
import numpy as np
from scipy.optimize import fmin

MIN_POINTS_FOR_ALIGNMENT = 6

# TODO: better handling for relatively small numbers of pins


class UnipuckTemplate:
    """ Defines the layout of a type of sample holder that is a circular puck
    that contains concentric circles (layers) of sample pins.
    """
    def __init__(self):
        self.slots = 16
        self.puck_radius = 1
        self.center_radius = 0.151  # radius of puck center (relative to puck radius)
        self.slot_radius = 0.197  # radius of a pin slot (relative to puck radius)
        self.layers = 2  # number of concentric layers of pin slots
        self.n = [5, 11]  # number of pin slots in each concentric layer, starting from center
        self.layer_radii = [0.371, 0.788]  # distance of center of a pin of a given concentric layer from center of puck


class Unipuck:
    def __init__(self, pin_centers):
        self.template = UnipuckTemplate()
        self.num_slots = self.template.slots
        self._pin_centers = pin_centers

        self.aligned = False
        self.error = None

        if len(pin_centers) >= MIN_POINTS_FOR_ALIGNMENT:
            self._perform_alignment()
        else:
            self.error = "Not enough pins for alignment"

    def is_aligned(self):
        return self.aligned

    def draw_plate(self, cvimg, color):
        cvimg.draw_dot(self._puck_center, color)
        cvimg.draw_circle(self._puck_center, self._puck_radius, color)
        cvimg.draw_circle(self._puck_center, self._center_radius, color)
        for center in self._template_centers:
            cvimg.draw_dot(center, color)
            cvimg.draw_circle(center, self._slot_radius, color)

    def draw_pin_highlight(self, cvimg, color, pin_number):
        center = self._template_centers[pin_number - 1]
        cvimg.draw_circle(center, self._slot_radius, color, thickness=int(self._slot_radius * 0.2))
        cvimg.draw_text(str(pin_number), center, color, centered=True)

    def crop_image(self, cvimg):
        cvimg.crop_image(self._puck_center, 1.1 * self._puck_radius)

    def closest_slot(self, point):
        slot_sq = self._slot_radius * self._slot_radius
        for i, center in  enumerate(self._template_centers):
            # slots are non-overlapping so if its in the slot radius, it must be the closest
            if distance_sq(center, point) < slot_sq:
                return i+1

        return 0

    def _perform_alignment(self):
        try:
            self._puck_center = Unipuck._find_puck_center(self._pin_centers)
            self._puck_radius = Unipuck._calculate_puck_size(self._pin_centers, self._puck_center, self.template)

            self._template_centers = []
            self._rotation = 0

            self._scale = self._puck_radius
            self._center_radius = self._scale * self.template.center_radius
            self._slot_radius = self._scale * self.template.slot_radius

            self._determine_puck_orientation()
        except Exception as ex:
            self.error = ex.message

    @staticmethod
    def _find_puck_center(pin_centers):
        """Calculate approximate center point of the puck from positions of the center points
        of the pin slots.

        Within each layer there may be some missing points, so if we calculate the center
        position of the puck by averaging the center positions of the slots, the results will
        be a bit out. Instead, we use the average center position (the centroid) as a starting
        point and divide the slots into two groups based on how close they are to the centroid.
        As long as not too many slots are missing, the division into groups should work well.
        We then iterate over different values for the puck center position, attempting to find
        a location that is equidistant from all of the slot centers.
        """
        centroid = calculate_centroid(pin_centers)

        # Calculate distance from center to each pin-center
        distances = [[p,distance(p, centroid)] for p in pin_centers]
        distances = sorted(distances, key=lambda distance: distance[1])
        layer_break = _partition([d for p, d in distances])

        first_layer = [[x,y] for (x,y), d in distances[:layer_break]]
        second_layer = [[x,y] for (x,y), d in distances[layer_break:]]
        layer = first_layer if len(first_layer) > len(second_layer) else second_layer

        # For the outer layer, perform a minimisation
        center = fmin(func=_center_minimiser, x0=centroid, args=tuple([[first_layer, second_layer]]), xtol=1, disp=False)
        center = tuple([int(center[0]), int(center[1])])

        return center


    @staticmethod
    def _calculate_puck_size(pin_centers, puck_center, template):
        """Calculate the size of the puck in image pixels.
        First determine the average distance from the puck center to each layer, then infer the
        puck size from this through knowledge of the puck's geometry
        """
        # calculate distance from center to each pin-center
        distances = [distance(p, puck_center) for p in pin_centers]
        distances.sort()
        layer_break = _partition(distances)

        if len(distances) > template.slots:
            raise Exception("Too many puck slots detected")

        first_layer = distances[:layer_break]
        second_layer = distances[layer_break:]

        second_layer_radius = np.median(np.array(second_layer))
        puck_radius = int(second_layer_radius / template.layer_radii[1])
        return puck_radius

    def _determine_puck_orientation(self):
        """Determine orientation of puck template - inefficient algorithm for the moment but works OK.
        Try the template a set of incremental rotations and determine which is the best orientation
        but looking at sum of squared errors
        """
        # find errors
        errors = []
        best_sse = 10000000
        best_angle = 0
        for a in range(360):
            angle = a / (180 / math.pi)
            self._set_rotation(angle)
            sse = 0
            for p in self._pin_centers:
                sse += self._shortest_sq_distance(p)
            if sse < best_sse:
                best_sse = sse
                best_angle = angle

            errors.append([angle, sse])

        average_error = best_sse / self._puck_radius ** 2 / len(self._pin_centers)
        if average_error < 0.003:
            self.aligned = True
        else:
            self.aligned = False
            self.error = "Failed to align puck"

        self._set_rotation(best_angle)


    def _set_rotation(self, angle):
        self._rotation = angle
        # calculate pin slot locations
        n = self.template.n
        r = self.template.layer_radii
        center = self._puck_center
        self._template_centers = []
        for i, num in enumerate(n):
            radius = r[i] * self._scale
            for j in range(num):
                angle = (2.0 * math.pi * -j / num) - (math.pi / 2.0) + self._rotation
                point = tuple([int(center[0] + radius * math.cos(angle)),  int(center[1] + radius * math.sin(angle))])
                self._template_centers.append(point)

    def _shortest_sq_distance(self, point):
        """returns the distance to the closest slot center point"""
        low_l_sq = 100000000
        slot_sq = self._slot_radius * self._slot_radius
        for c in self._template_centers:
            length_sq = distance_sq(c, point)
            if length_sq < low_l_sq:
                low_l_sq = length_sq
                # slots are non-overlapping so if its in the slot radius, it must be the closest
                if length_sq < slot_sq:
                    return length_sq

        return low_l_sq


def distance(a, b):
    x = a[0]-b[0]
    y = a[1]-b[1]
    return int(math.sqrt(x**2+y**2))


def distance_sq(a,b):
    x = a[0]-b[0]
    y = a[1]-b[1]
    return x**2+y**2


def calculate_centroid(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    return (int(sum(x) / len(points)), int(sum(y) / len(points)))


def _center_minimiser(center, layers):
    errors = []
    for layer in layers:
        distances = [distance_sq(p, center) for p in layer]
        distances.sort()

        if not any(distances):
            print "EMPTY MEAN"

        mean = np.mean(distances)
        layer_errors = [(d-mean)**2 for d in distances]
        errors.extend(layer_errors)

    return sum(errors)


def _partition(numbers):
    """Splits a list of numbers into two groups. Assumes the numbers are samples randomly
    around one of two median values. Used to split the
    """
    if len(numbers) < 3:
        return 0
    numbers.sort()
    s = 0
    break_point = 0
    while s < len(numbers):
        if not numbers[:s+1] or not numbers[-s-1:]:
            raise Exception("Empty slice")

        av1 = np.mean(numbers[:s+1])
        av2 = np.mean(numbers[-s-1:])
        s += 1
        if (numbers[s] - av1) > (av2 - numbers[s]):
            break_point = s
            break

    return break_point