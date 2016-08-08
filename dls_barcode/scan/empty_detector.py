from util.cv import CircleDetector
from util.image import Color


class EmptySlotDetector:
    def __init__(self):
        pass

    @staticmethod
    def detect(image, barcodes):
        if len(barcodes) == 0:
            return []

        avg_radius = sum([b.radius() for b in barcodes]) / len(barcodes)

        circles = EmptySlotDetector._hole_detection(image, avg_radius)

        # Exclude any points that overlap known barcode locations
        bc_centers = [bc.center() for bc in barcodes]
        empty_circles = []
        for circle in circles:
            contains = [circle.contains_point(bc) for bc in bc_centers]
            if not any(contains):
                empty_circles.append(circle)

        DEBUG = True
        if DEBUG:
            copy_image = image.to_color().copy()
            EmptySlotDetector.draw_circles(copy_image, empty_circles, avg_radius)

            puck_circles = EmptySlotDetector._puck_detection(image, avg_radius * 10)
            EmptySlotDetector.draw_circles(copy_image, puck_circles, avg_radius)
            copy_image.popup()

        return empty_circles

    @staticmethod
    def _hole_detection(image, avg_barcode_radius):
        # For Unipuck, empty hole radius is about 1.1-1.3 x barcode radius
        MIN_FACTOR = 1.00
        MAX_FACTOR = 1.50

        # For Unipuck, separation between closest neighbours is about 3.7-3.9 x barcode radius
        SEPARATION_FACTOR = 3.6

        min_radius = MIN_FACTOR * avg_barcode_radius
        max_radius = MAX_FACTOR * avg_barcode_radius
        min_dist = SEPARATION_FACTOR * avg_barcode_radius

        detector = CircleDetector()
        detector.set_minimum_radius(min_radius)
        detector.set_maximum_radius(max_radius)
        detector.set_minimum_separation(min_dist)
        circles = detector.find_circles(image)

        return circles

    @staticmethod
    def _puck_detection(image, approx_radius, tolerance=0.1):
        min_radius = approx_radius * (1-tolerance)
        max_radius = approx_radius * (1+tolerance)

        detector = CircleDetector()
        detector.set_minimum_separation(100000)
        detector.set_minimum_radius(min_radius)
        detector.set_maximum_radius(max_radius)

        circles = detector.find_circles(image)
        return circles

    @staticmethod
    def draw_circles(img, circles, avg_barcode_radius):
        for circle in circles:
            img.draw_circle(circle, Color.Red(), thickness=3)

            text = "{:.2f}".format(circle.radius() / avg_barcode_radius)
            img.draw_text(text, circle.center(), Color.Red(), True, 1, 1)

            # closest_distance = 100000
            # closest = None
            # for c2 in circles:
            #     if circle != c2:
            #         dist = circle.center().distance_to(c2.center())
            #         if dist < closest_distance:
            #             closest = c2
            #             closest_distance = dist
            #
            #         if dist < 4.4 * avg_barcode_radius:
            #             img.draw_line(circle.center(), c2.center(), Color.Red())
            #
            # if closest is not None:
            #     text = "{:.2f}".format(closest_distance / avg_barcode_radius)
            #     img.draw_text(text, circle.center(), Color.Green(), True, 1, 1)
