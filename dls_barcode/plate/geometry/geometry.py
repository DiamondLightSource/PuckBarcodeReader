from .exception import GeometryException
from .unipuck import Unipuck
from .unipuck_calculator import UnipuckCalculator
from .blank import BlankGeometry


class Geometry:
    NO_GEOMETRY = BlankGeometry.TYPE_NAME
    UNIPUCK = Unipuck.TYPE_NAME

    TYPES = [UNIPUCK]

    _MSG_NOT_IMPLEMENTED = "Geometry Type '{}' not implemented"
    _MSG_UNKNOWN = "Unknown Geometry Type: '{}'"

    @staticmethod
    def get_class(geo_name):
        if geo_name == Geometry.NO_GEOMETRY:
            Geometry._raise_not_implemented(geo_name)
        elif geo_name == Geometry.UNIPUCK:
            return Unipuck
        else:
            Geometry._raise_unknown(geo_name)

    @staticmethod
    def calculate_geometry(geo_name, slot_centers):
        if geo_name == Geometry.NO_GEOMETRY:
            Geometry._raise_not_implemented(geo_name)
        elif geo_name == Geometry.UNIPUCK:
            calculator = UnipuckCalculator(slot_centers)
            geometry = calculator.perform_alignment()
            return geometry
        else:
            Geometry._raise_unknown(geo_name)

    @staticmethod
    def get_num_slots(geo_name):
        cls = Geometry.get_class(geo_name)
        return cls.NUM_SLOTS

    @staticmethod
    def _raise_not_implemented(geo_name):
        raise GeometryException(Geometry._MSG_NOT_IMPLEMENTED.format(geo_name))

    @staticmethod
    def _raise_unknown(geo_name):
        raise GeometryException(Geometry._MSG_UNKNOWN.format(geo_name))
