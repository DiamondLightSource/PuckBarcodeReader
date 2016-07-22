import numpy as np

from dls_barcode.plate import Unipuck
from dls_barcode.util import Transform


class GeometryAdjuster:
    def adjust(self, plate, barcodes):
        # TODO: document this method

        # If we don't have 2 common barcodes, we can't realign, so return a blank geometry (which
        # will cause this frame to be skipped).
        valid_barcodes = [bc for bc in barcodes if bc.is_read() and bc.is_valid()]
        if len(valid_barcodes) < 2:
            print("ALIGNMENT ADJUSTMENT FAIL")  # DEBUG
            return Unipuck.from_pin_centers([])

        print("ALIGNMENT ADJUSTMENT")  # DEBUG

        line_transform = self._determine_old_to_new_transformation(plate, valid_barcodes)
        transformed_centers = self._transform_barcode_centers(plate, line_transform)
        new_centers = self._get_transformed_barcode_centers_list(barcodes, transformed_centers)
        geometry = Unipuck.from_pin_centers(new_centers)

        return geometry

    def _determine_old_to_new_transformation(self, plate, valid_barcodes):
        # Get the positions of the two common barcodes in the current frame and the previous one
        barcode_a = valid_barcodes[0]
        barcode_b = valid_barcodes[1]
        pos_a_new = barcode_a.center()
        pos_b_new = barcode_b.center()
        pos_a_old = None
        pos_b_old = None

        for slot in plate._slots:
            if slot.barcode_data() == barcode_a.data():
                pos_a_old = slot.barcode_position()
            elif slot.barcode_data() == barcode_b.data():
                pos_b_old = slot.barcode_position()

        # Determine the transformation that maps the old points to the new
        line_transform = Transform.line_mapping(pos_a_old, pos_b_old, pos_a_new, pos_b_new)
        return line_transform

    def _transform_barcode_centers(self, plate, transformation):
        transformed_bc_centers = []
        for slot in plate._slots:
            center = slot.barcode_position()
            if center:
                transformed_center = transformation.transform(center)
                transformed_bc_centers.append(transformed_center)

        return transformed_bc_centers

    def _get_transformed_barcode_centers_list(self, barcodes, transformed_centers):
        # Replace any transformed points which overlap new fp centers
        new_centers = [bc.center() for bc in barcodes]
        radius_sq = self._mean_square_barcode_radius(barcodes)
        for old_center in transformed_centers:
            overlap = False
            for bc in barcodes:
                overlap |= self._does_barcode_overlap_point(bc, old_center, radius_sq)

            if not overlap:
                new_centers.append(old_center)

        return new_centers

    def _does_barcode_overlap_point(self, bc, old_center, radius_sq):
        new_center = bc.center()
        distance = (new_center[0] - old_center[0]) ** 2 + (new_center[1] - old_center[1]) ** 2
        does_overlap = distance < radius_sq
        return does_overlap

    def _mean_square_barcode_radius(self, barcodes):
        return np.mean([bc.radius() for bc in barcodes]) ** 2