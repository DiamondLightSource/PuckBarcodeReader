import logging
import numpy as np

from dls_barcode.geometry.unipuck_calculator import UnipuckCalculator
from dls_util.transform import Transform


class GeometryAdjustmentError(Exception):
    pass


class UnipuckGeometryAdjuster:
    """ Occasionally the situation arises that results of the unipuck geometry calculation are different
     for two consecutive frames. This means that in at least one of these frames, the orientation has
     not been calculated correctly (due to uncertainty in the observed slot positions).

    In this case, the set of already known barcodes will not map properly between the correct slot numbers.
    We therefore make an adjustment to the geometry to map the positions of the barcodes in the old frame to
    those in the new one.

    An incorrectly calculated geometry is unusual so will likely not last for more than a frame or two before
    the correct geometry is found again.
    """
    def adjust(self, plate, barcodes):
        # TODO: refactor and document this method
        log = logging.getLogger(".".join([__name__]))

        # If we don't have 2 common barcodes, we can't realign, so return a blank geometry (which
        # will cause this frame to be skipped).
        valid_barcodes = [bc for bc in barcodes if bc.is_read() and bc.is_valid()]
        if len(valid_barcodes) < 2:
            log.debug("Geometry adjustment failed.")
            raise GeometryAdjustmentError("Geometry adjustment failed.")

        log.debug("ALIGNMENT ADJUSTMENT")  # DEBUG

        line_transform = self._determine_old_to_new_transformation(plate, valid_barcodes)
        transformed_centers = self._transform_barcode_centers(plate, line_transform)
        new_centers = self._get_transformed_barcode_centers_list(barcodes, transformed_centers)

        calculator = UnipuckCalculator(new_centers)
        geometry = calculator.perform_alignment()

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
        distance = new_center.distance_to_sq(old_center)
        does_overlap = distance < radius_sq
        return does_overlap

    def _mean_square_barcode_radius(self, barcodes):
        return np.mean([bc.radius() for bc in barcodes]) ** 2
