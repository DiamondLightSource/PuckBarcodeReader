from __future__ import division
import math
import numpy as np
from scipy.optimize import fmin


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
    def __init__(self, pin_circles, pin_rois, uncircled_pins=None):
        if uncircled_pins is None:
            uncircled_pins = []

        self.template = UnipuckTemplate()
        self.num_slots = self.template.slots

        self.pin_circles = pin_circles
        self.pin_rois = pin_rois
        self.puck_center = Unipuck._puck_center_from_pin_circles(pin_circles, uncircled_pins)
        self.puck_radius = Unipuck._calculate_puck_size(pin_circles, self.puck_center, self.template)

        self.template_centers = []
        self.scale = self.puck_radius
        self.rotation = 0

        self.puck_radius = self.scale
        self.center_radius = self.scale * self.template.center_radius
        self.slot_radius = self.scale * self.template.slot_radius

        self.aligned = False
        self.error = None

        try:
            self._determine_puck_orientation()
        except Exception as ex:
            self.error = ex.message

    def draw_plate(self, cvimg, color):
        cvimg.draw_dot(self.puck_center, color)
        cvimg.draw_circle(self.puck_center, self.puck_radius, color)
        cvimg.draw_circle(self.puck_center, self.center_radius, color)
        for center in self.template_centers:
            cvimg.draw_dot(center, color)
            cvimg.draw_circle(center, self.slot_radius, color)

    def draw_pins(self, cvimg, color):
        for circle in self.pin_circles:
            cvimg.draw_circle(center=circle[0], radius=circle[1], color=color)
            cvimg.draw_dot(center=circle[0], color=color)

        # Draw the region of interest squares around each pin
        for roi in self.pin_rois:
            cvimg.draw_rectangle(roi, color)

    def crop_image(self, cvimg):
        cvimg.crop_image(self.puck_center, 1.1*self.puck_radius)

    def closest_slot(self, point):
        slot_sq = self.slot_radius * self.slot_radius
        for i, center in  enumerate(self.template_centers):
            # slots are non-overlapping so if its in the slot radius, it must be the closest
            if distance_sq(center, point) < slot_sq:
                return i+1

        return 0

    @staticmethod
    def _puck_center_from_pin_circles(pin_circles, uncircled_pins):
        """Calculate approximate center point of the puck from positions of some (or all) of the
        center points of the pin slots.

        Within each layer there may be some missing points, so if we calculate the center
        position of the puck by averaging the center
        positions of the slots, the results will be a bit out. Instead, we use the average
        center position (the centroid) as a starting point and divide the slots into
        two groups based on how close they are to the centroid. As long as not too many slots
        are missing, the division into groups should work well. We then iterate over different
        values for the puck center position, attempting to find a location that is equidistant
        from all of the slot centers.
        """
        pin_centers = [circle[0] for circle in pin_circles]
        pin_centers.extend((uncircled_pins))
        centroid = calculate_centroid(pin_centers)

        # calculate distance from center to each pin-center
        distances = [[p,distance(p, centroid)] for p in pin_centers]
        distances = sorted(distances, key=lambda distance: distance[1])
        layer_break = _partition([d for p, d in distances])

        first_layer = [[x,y] for (x,y), d in distances[:layer_break]]
        second_layer = [[x,y] for (x,y), d in distances[layer_break:]]
        layer = first_layer if len(first_layer) > len(second_layer) else second_layer

        #for the outer layer, perform a minimisation
        center = fmin(func=_center_minimiser, x0=centroid, args=tuple([[first_layer, second_layer]]), xtol=1, disp=False)
        center = tuple([int(center[0]), int(center[1])])

        return center


    @staticmethod
    def _calculate_puck_size(pin_circles, center, template):
        """Calculate the size of the puck in image pixels.
        First determine the average distance from the puck center to each layer, then infer the
        puck size from this through knowledge of the puck's geometry
        """
        # calculate distance from center to each pin-center
        distances = [distance(p[0], center) for p in pin_circles]
        distances.sort()
        layer_break = _partition(distances)

        if len(distances) > template.slots:
            raise Exception("Too many puck slots detected")

        first_layer = distances[:layer_break]
        second_layer = distances[layer_break:]

        # todo: this currently assumes a Unipuck
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
        pin_centers = [circle[0] for circle in self.pin_circles]
        for a in range(360):
            angle = a / (180 / math.pi)
            self._set_rotation(angle)
            sse = 0
            for p in pin_centers:
                sse += self._shortest_sq_distance(p)
            if sse < best_sse:
                best_sse = sse
                best_angle = angle

            errors.append([angle, sse])

        average_error = best_sse / self.puck_radius**2 / len(pin_centers)
        if average_error < 0.003:
            self.aligned = True
        else:
            raise Exception("Failed to align puck")
            self.aligned = False

        self._set_rotation(best_angle)


    def _set_rotation(self, angle):
        self.rotation = angle
        # calculate pin slot locations
        n = self.template.n
        r = self.template.layer_radii
        center = self.puck_center
        self.template_centers = []
        for i, num in enumerate(n):
            radius = r[i] * self.scale
            for j in range(num):
                angle = (2.0 * math.pi * -j / num) - (math.pi / 2.0) + self.rotation
                point = tuple([int(center[0] + radius * math.cos(angle)),  int(center[1] + radius * math.sin(angle))])
                self.template_centers.append(point)

    def _shortest_sq_distance(self, point):
        """returns the distance to the closest slot center point"""
        low_l_sq = 100000000
        slot_sq = self.slot_radius * self.slot_radius
        for c in self.template_centers:
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
        av1 = np.mean(numbers[:s+1])
        av2 = np.mean(numbers[-s-1:])
        s += 1
        if (numbers[s] - av1) > (av2 - numbers[s]):
            break_point = s
            break

    return break_point