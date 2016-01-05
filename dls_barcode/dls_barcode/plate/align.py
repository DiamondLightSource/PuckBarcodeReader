from dls_barcode.image import CvImage
from cps_puck import Puck


class Aligner:
    def get_plate(self, grayscale_image, barcodes):
        """Align the puck to find the correct slot number for each datamatrix
        """
        # Find the average radius of the barcode symbols
        barcode_bounds = [barcode.bounds for barcode in barcodes]
        radii = [r for (c, r) in barcode_bounds]
        avg_radius = sum(radii) / len(radii)

        uncircled_pins = []
        pin_circles = []
        pin_rois = [];
        for (center, radius) in barcode_bounds:
            # Get region of image that fully contains the pin
            r = 2.5 * radius
            sub_img, roi = CvImage.sub_image(grayscale_image, center, r)
            pin_rois.append(roi)

            # Find circle in the sub image
            circle = CvImage.find_circle(sub_img, avg_radius, 2*avg_radius)
            if circle:
                circle[0][0] += roi[0]
                circle[0][1] += roi[1]
                pin_circles.append(circle)
            else:
                uncircled_pins.append(center)

        if not pin_circles:
            raise Exception("No puck slots detected")

        # Create representation of the puck based on positions of the pins
        puck = Puck(barcodes, pin_circles, pin_rois, uncircled_pins)

        return puck

    def get_slot_number(self, puck, center):
        return puck.closest_slot(center)









