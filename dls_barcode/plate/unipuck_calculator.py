from __future__ import division
import math
import numpy as np
from scipy.optimize import fmin

from .unipuck import Unipuck, UnipuckTemplate

MIN_POINTS_FOR_ALIGNMENT = 6


class UnipuckCalculator:
    """ Creates a Unipuck object, determining its size, position, and orientation. This is all
    calculated from knowledge of the positions of the datamatrix barcodes within the image,
    since each barcode is assumed to be printed on the top of a sample pin and will be
    positioned roughly in the center of a puck slot.

    The puck has no rotational symmetry, so if one knows the approximate position of the
    center of each slot, the unique orientation and position of the puck can be determined.
    This is possible even if some of the slot locations are not none.
    """
    def __init__(self, pin_centers):
        """ Determine the puck geometry (position and orientation) for the locations of the
        centers of some (or all of the pins).
        """
        self._num_slots = UnipuckTemplate.NUM_SLOTS

        self._pin_centers = pin_centers
        self.error = None

    def perform_alignment(self):
        puck = None
        num_points = len(self._pin_centers)
        if num_points > self._num_slots:
            self.error = "Too many pins to perform alignment"
        elif num_points < MIN_POINTS_FOR_ALIGNMENT:
            self.error = "Not enough pins to perform alignment"
        else:
            puck = self._calculate_puck_alignment()

        return puck

    def _calculate_puck_alignment(self):
        """ Determine the puck geometry (position and orientation) for the locations of the
        centers of some (or all of the pins).
        """
        try:
            center = self._find_puck_center(self._pin_centers)
            radius = self._calculate_puck_size(self._pin_centers, center)

            puck = Unipuck(center, radius)

            angle, error = self._determine_puck_orientation(puck, self._pin_centers)
            puck.set_rotation(angle)
            self.error = error

            return puck

        except Exception as ex:
            self.error = ex.message()
            return None

    @staticmethod
    def _find_puck_center(pin_centers):
        """ Calculate approximate center point of the puck from positions of the center points
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
        distances = [[p, distance(p, centroid)] for p in pin_centers]
        distances = sorted(distances, key=lambda distance: distance[1])

        # Sort the points into two layers based on their distance from the centroid
        layer_break = _partition([d for p, d in distances])
        first_layer = [[x, y] for (x, y), d in distances[:layer_break]]
        second_layer = [[x, y] for (x, y), d in distances[layer_break:]]

        # Optimise for the puck center by finding the point that is equidistant from every point in each layer
        center = fmin(func=_center_minimiser, x0=centroid, args=tuple([[first_layer, second_layer]]), xtol=1, disp=False)
        center = tuple([int(center[0]), int(center[1])])

        return center

    @staticmethod
    def _calculate_puck_size(pin_centers, puck_center):
        """ Calculate the radius of the puck in image pixels. First determine the average distance
        from the puck center to each layer, then infer the puck size from this through knowledge
        of the puck's geometry.
        """
        # Calculate distance from center to each pin-center
        distances = [distance(p, puck_center) for p in pin_centers]
        layer_break = _partition(distances)
        second_layer = distances[layer_break:]

        # Determine the puck radius based on the average second layer radius in the image
        second_layer_radius = np.median(np.array(second_layer))
        puck_radius = int(second_layer_radius / UnipuckTemplate.LAYER_RADII[1])
        return puck_radius

    @staticmethod
    def _determine_puck_orientation(puck, pin_centers):
        """ Using the known size and position of the puck in the image, determine the correct
        orientation of puck. Try the template at a set of incremental rotations and determine
        which is the best orientation by looking at sum of squared errors. This algorithm can
        definitely be improved upon but this does the job
        """
        # TODO: finding orientation takes 80-90% of the alignment time; find a better algorithm

        errors = []
        best_sse = 10000000
        best_angle = 0
        original_angle = puck.angle()
        error_msg = None

        # For each angular increment, calculate the sum of squared errors in slot center position
        for a in range(0, 360, 2):
            angle = a / (180 / math.pi)
            puck.set_rotation(angle)
            sse = 0
            for p in pin_centers:
                sse += UnipuckCalculator._shortest_sq_distance(puck, p)
            if sse < best_sse:
                best_sse = sse
                best_angle = angle
            errors.append([angle, sse])

        average_error = best_sse / puck.radius() ** 2 / len(pin_centers)
        if average_error < 0.003:
            puck.set_aligned(True)
        else:
            puck.set_aligned(False)
            error_msg = "Failed to align puck"

        puck.set_rotation(original_angle)

        return best_angle, error_msg

    @staticmethod
    def _shortest_sq_distance(puck, point):
        """ Returns the distance from the specified point to the closest slot in the puck. """
        low_l_sq = 100000000
        slot_sq = puck.slot_radius()**2

        for num in range(puck.num_slots()):
            center = puck.slot_center(num+1)
            length_sq = distance_sq(center, point)
            if length_sq < low_l_sq:
                low_l_sq = length_sq
                # Slots are non-overlapping so if its in the slot radius, it must be the closest
                if length_sq < slot_sq:
                    return length_sq

        return low_l_sq


def distance(a, b):
    """ Calculates the distance between a and b. This operation is relatively expensive as it
    contains a square root. If comparing distances, use distance_sq instead as its cheaper.
    """
    x = a[0]-b[0]
    y = a[1]-b[1]
    return int(math.sqrt(x**2+y**2))


def distance_sq(a, b):
    """ Calculates the square of the distance from a to b.
    """
    x = a[0]-b[0]
    y = a[1]-b[1]
    return x**2+y**2


def calculate_centroid(points):
    """ Calculates the centroid (average center position) of the specified points.
    """
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    return int(sum(x) / len(points)), int(sum(y) / len(points))


def _center_minimiser(center, layers):
    """ Used as the cost function in an optimisation routine. The puck consists of 2 layers of slots.
    Within a given layer, each slot is the same distance from the center point of the puck. Therefore
    for a trial center point, we calculate an error that is the sum of the squares of the deviation
    of the distance of each slot from the mean distance of all the slots in the layer.
    """
    errors = []
    for layer in layers:
        distances = [distance_sq(p, center) for p in layer]

        mean = np.mean(distances)
        layer_errors = [(d-mean)**2 for d in distances]
        errors.extend(layer_errors)

    return sum(errors)


def _partition(numbers):
    """Splits a list of numbers into two groups. Assumes the numbers are samples randomly
    around one of two median values.

    Works by stepping through the sorted list until we find the cutoff point between the two
    groups. This is established by the point being closer to the average of the second group
    than the average of the first.
    """
    if len(numbers) < 3:
        return numbers, None

    numbers.sort()
    s = 0
    break_point = 0

    while s < len(numbers):
        if not numbers[:s+1] or not numbers[-s-1:]:
            raise Exception("Empty slice")

        gp1_average = np.mean(numbers[:s+1])
        gp2_average = np.mean(numbers[-s-1:])

        s += 1

        distance_from_av1 = numbers[s] - gp1_average
        distance_from_av2 = gp2_average - numbers[s]

        if distance_from_av1 > distance_from_av2:
            break_point = s
            break

    return break_point
