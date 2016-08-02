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

        bc_centers = [bc.center() for bc in barcodes]
        empty_circles = []
        for circle in circles:
            contains = [circle.contains_point(bc) for bc in bc_centers]
            if not any(contains):
                empty_circles.append(circle)

        DEBUG = False
        if DEBUG:
            copy_image = image.to_color().copy()
            EmptySlotDetector.draw_circles(copy_image, empty_circles)

            puck_circles = EmptySlotDetector._puck_detection(image, avg_radius * 10.5)
            EmptySlotDetector.draw_circles(copy_image, puck_circles)
            copy_image.popup()

        return empty_circles

    @staticmethod
    def _hole_detection(image, avg_barcode_radius, tolerance=0.2):
        HOLE_FACTOR = 0.9
        SEPARATION_FACTOR = 4

        hole_radius = HOLE_FACTOR * avg_barcode_radius
        min_radius = hole_radius * (1-tolerance)
        max_radius = hole_radius * 2
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
    def draw_circles(img, circles):
        for circle in circles:
            img.draw_circle(circle, Color.Red(), thickness=3)
