from __future__ import division
import math
import numpy as np
from scipy.optimize import fmin

MIN_POINTS_FOR_ALIGNMENT = 6


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
    """ Represents the geometry of a Unipuck within an image including the size, position,
    and orientation and the size and position of the puck's sample slots. This is all
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
        self._pin_centers = pin_centers
        self._template = UnipuckTemplate()
        self.num_slots = self._template.slots

        self._aligned = False
        self.error = None

        num_points = len(pin_centers)
        if num_points > self.num_slots:
            self.error = "Too many pins to perform alignment"
        elif num_points < MIN_POINTS_FOR_ALIGNMENT:
            self.error = "Not enough pins to perform alignment"
        else:
            self._perform_alignment()

    def is_aligned(self):
        """ True if the puck geometry has been successfully aligned to the image.
        """
        return self._aligned

    def draw_plate(self, cvimg, color):
        """ Draws an outline of the puck on the supplied image including the locations of the slots.
        """
        cvimg.draw_dot(self._puck_center, color)
        cvimg.draw_circle(self._puck_center, self._puck_radius, color, thickness=int(0.05*self._puck_radius))
        cvimg.draw_circle(self._puck_center, self._center_radius, color)
        for center in self._template_centers:
            cvimg.draw_dot(center, color)
            cvimg.draw_circle(center, self._slot_radius, color)

    def draw_pin_highlight(self, cvimg, color, pin_number):
        """ Draws a highlight circle and slot number for the specified slot on the image.
        """
        center = self._template_centers[pin_number - 1]
        cvimg.draw_circle(center, self._slot_radius, color, thickness=int(self._slot_radius * 0.2))
        cvimg.draw_text(str(pin_number), center, color, centered=True)

    def crop_image(self, cvimg):
        """ Crops the image to the area which contains the puck.
        """
        cvimg.crop_image(self._puck_center, 1.1 * self._puck_radius)

    def containing_slot(self, point):
        """ Returns the number of the slot which contains the specified point or 0 otherwise.
        """
        slot_sq = self._slot_radius * self._slot_radius
        for i, center in  enumerate(self._template_centers):
            # slots are non-overlapping so if its in the slot radius, it must be the closest
            if distance_sq(center, point) < slot_sq:
                return i+1

        return None

    def _perform_alignment(self):
        """ Determine the puck geometry (position and orientation) for the locations of the
        centers of some (or all of the pins).
        """
        try:
            self._puck_center = Unipuck._find_puck_center(self._pin_centers)
            self._puck_radius = Unipuck._calculate_puck_size(self._pin_centers, self._puck_center, self._template)
            self._template_centers = []
            self._rotation = 0

            self._scale = self._puck_radius
            self._center_radius = self._scale * self._template.center_radius
            self._slot_radius = self._scale * self._template.slot_radius

            self._determine_puck_orientation()
        except Exception as ex:
            self.error = ex.message

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
        distances = [[p,distance(p, centroid)] for p in pin_centers]
        distances = sorted(distances, key=lambda distance: distance[1])

        # Sort the points into two layers based on their distance from the centroid
        layer_break = _partition([d for p, d in distances])
        first_layer = [[x,y] for (x,y), d in distances[:layer_break]]
        second_layer = [[x,y] for (x,y), d in distances[layer_break:]]

        # Optimise for the puck center by finding the point that is equidistant from every point in each layer
        center = fmin(func=_center_minimiser, x0=centroid, args=tuple([[first_layer, second_layer]]), xtol=1, disp=False)
        center = tuple([int(center[0]), int(center[1])])

        return center

    @staticmethod
    def _calculate_puck_size(pin_centers, puck_center, template):
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
        puck_radius = int(second_layer_radius / template.layer_radii[1])
        return puck_radius

    def _determine_puck_orientation(self):
        """ Using the known size and position of the puck in the image, determine the correct
        orientation of puck. Try the template at a set of incremental rotations and determine
        which is the best orientation by looking at sum of squared errors. This algorithm can
        definitely be improved upon but this does the job
        """
        # TODO: finding orientation takes 80-90% of the alignment time; find a better algorithm

        errors = []
        best_sse = 10000000
        best_angle = 0

        # For each angular increment, calculate the sum of squared errors in slot center position
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
            self._aligned = True
        else:
            self._aligned = False
            self.error = "Failed to align puck"






        # ------- METHOD 3 ------------


        # get points in outer layer
        distances = [[p,distance_sq(p, self._puck_center)] for p in self._pin_centers]
        distances = sorted(distances, key=lambda distance: distance[1])
        layer_break = _partition([d for p, d in distances])
        first_layer = [[x,y] for (x,y), d in distances[:layer_break]]
        second_layer = [[x,y] for (x,y), d in distances[layer_break:]]

        # calculate angles from north:
        center = self._puck_center
        layer_1_angles = []
        layer_2_angles = []
        for point in first_layer:
            theta = math.atan2((point[0]-center[0]), (point[1]-center[1])) + math.pi
            layer_1_angles.append(theta)
        for point in second_layer:
            theta = math.atan2((point[0]-center[0]), (point[1]-center[1])) + math.pi
            layer_2_angles.append(theta)

        layer_1_angles.sort()
        layer_2_angles.sort()

        del_5 = math.pi*2.0/5.0
        del_11 = math.pi*2.0/11.0

        layer_1_errors = [a % del_5 for a in layer_1_angles]
        layer_2_errors = [a % del_11 for a in layer_2_angles]

        l1_mean = np.mean(layer_1_errors)
        l2_mean = np.mean(layer_2_errors)

        a = [(2*math.pi)-(l1_mean+i*del_5) for i in range(5)]
        b = [(2*math.pi)-(l2_mean+i*del_11) for i in range(11)]
        newest_best_angle = self._average_of_closest_pair(a,b)


        # THIS WORKS, REMOVE THE OLD METHOD


        print "NEWEST", newest_best_angle, best_angle



        self._set_rotation(best_angle)

    def _distance_to_closest_angle(self, number, angles):
        best = 100
        for a in angles:
            dist = math.fabs(number-a) % (2.0* math.pi)
            if dist < best:
                best = dist
        return best

    def _average_of_closest_pair(self, a, b):
        nums = a + b
        nums.sort()
        best_i = -1
        best_diff = 100000
        for i in range(len(nums)-1):
            if nums[i+1] - nums[i] < best_diff:
                best_diff = nums[i+1] - nums[i]
                best_i = i

        return (nums[best_i+1] + nums[best_i]) / 2



    def _set_rotation(self, angle):
        """ Set the orientation of the puck template to the specified angle. Recalculate the
        positions of the slots.
        """
        self._rotation = angle

        # Calculate pin slot locations
        n = self._template.n
        r = self._template.layer_radii
        center = self._puck_center
        self._template_centers = []
        for i, num in enumerate(n):
            radius = r[i] * self._scale
            for j in range(num):
                angle = (2.0 * math.pi * -j / num) - (math.pi / 2.0) + self._rotation
                point = tuple([int(center[0] + radius * math.cos(angle)),  int(center[1] + radius * math.sin(angle))])
                self._template_centers.append(point)

    def _shortest_sq_distance(self, point):
        """ Returns the distance from the specified point to the closest slot in the template
        """
        low_l_sq = 100000000
        slot_sq = self._slot_radius * self._slot_radius
        for c in self._template_centers:
            length_sq = distance_sq(c, point)
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
    return (int(sum(x) / len(points)), int(sum(y) / len(points)))


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
    around one of two median values. Used to split the
    """
    if len(numbers) < 3:
        return numbers, None

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