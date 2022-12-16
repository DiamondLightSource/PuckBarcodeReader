import logging
from .exception import GeometryException
from .blank import BlankGeometry
from .unipuck import Unipuck
from .unipuck_calculator import UnipuckCalculator


class Geometry:
    """ Provides access to the various sample plate geometry classes.
    """
    NO_GEOMETRY = BlankGeometry.TYPE_NAME
    UNIPUCK = Unipuck.TYPE_NAME

    TYPES = [NO_GEOMETRY, UNIPUCK]

    _MSG_NOT_IMPLEMENTED = "Geometry Type '{}' not implemented"
    _MSG_UNKNOWN = "Unknown Geometry Type: '{}'"

    @staticmethod
    def get_class(geo_name):
        """ Get the geometry class based on its name. """
        if geo_name == Geometry.NO_GEOMETRY:
            return BlankGeometry
        elif geo_name == Geometry.UNIPUCK:
            return Unipuck
        else:
            Geometry._raise_unknown(geo_name)

    @staticmethod
    def calculate_geometry(geo_name, slot_centers):
        """ Create a geometry object of the specified type and calculate its layout based on the set of
        known slot positions."""
        if geo_name == Geometry.NO_GEOMETRY:
            return BlankGeometry(slot_centers)
        elif geo_name == Geometry.UNIPUCK:
            calculator = UnipuckCalculator(slot_centers)
            geometry = calculator.perform_alignment()
            return geometry
        else:
            Geometry._raise_unknown(geo_name)

    @staticmethod
    def get_num_slots(geo_name):
        """ Get the number of slots that a particular geometry type contains. """
        cls = Geometry.get_class(geo_name)
        return cls.NUM_SLOTS

    @staticmethod
    def _raise_not_implemented(geo_name):
        log = logging.getLogger(".".join([__name__]))
        log.debug(Geometry._MSG_NOT_IMPLEMENTED.format(geo_name))
        raise GeometryException(Geometry._MSG_NOT_IMPLEMENTED.format(geo_name))

    @staticmethod
    def _raise_unknown(geo_name):
        log = logging.getLogger(".".join([__name__]))
        log.debug(Geometry._MSG_UNKNOWN.format(geo_name))
        raise GeometryException(Geometry._MSG_UNKNOWN.format(geo_name))
