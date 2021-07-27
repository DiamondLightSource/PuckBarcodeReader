import datetime
import time
import uuid

from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL
from dls_barcode.geometry import Geometry
from dls_util.image import Image, Color


class Record:
    """ Represents a record of a single scan, including the time, type of
    sample holder plate, list of barcodes scanned, and the path of the image
    of the scan (if any). Can be written to and read from file.
    """

    # Indices for ordering of data when a record is written to or read from a string
    IND_ID = 0
    IND_TIMESTAMP = 1
    IND_IMAGE = 2
    IND_HOLDER_IMAGE = 3
    IND_PLATE = 4
    IND_BARCODES = 5
    IND_GEOMETRY = 6
    NUM_RECORD_ITEMS = 7


    # Constants
    ITEM_SEPARATOR = ";"
    BC_SEPARATOR = ","
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    BAD_SYMBOLS = [EMPTY_SLOT_SYMBOL, NOT_FOUND_SLOT_SYMBOL]

    def __init__(self, plate_type, holder_barcode, barcodes, image_path, holder_image_path, geometry, timestamp=0.0, id=0):
        """
        :param plate_type: the type of the sample holder plate (string)
        :param holder_barcode: the barcode of the holder plate
        :param barcodes: ordered array of strings giving the barcodes in each slot
            of the plate in order. Empty slots should be denoted by empty strings.
        :param image_path: the absolute path of the image.
        :param timestamp: number of seconds since the epoch (use time.time(); generated
            automatically if a value isn't supplied
        :param id: uid for the record; one will be generated if not supplied
        """
        try:
            self.timestamp = float(timestamp)
        except ValueError:
            self.timestamp = 0.0

        self.image_path = image_path
        self.holder_image_path = holder_image_path
        self.plate_type = plate_type
        self.holder_barcode = holder_barcode
        self.barcodes = barcodes
        self.geometry = geometry
        self.id = str(id)

        # todo: find a work around for this (i.e. encode the semi colons)
        # Remove ";" from barcode data
        for i, bc in enumerate(self.barcodes):
            self.barcodes[i] = bc.replace(self.ITEM_SEPARATOR, "") # interesting where does ; come from?

        # Generate timestamp and uid if none are supplied
        if timestamp == 0:
            self.timestamp = time.time()

        if id == 0:
            self.id = str(uuid.uuid4())

        # Separate Date and Time
        dt = self._formatted_date().split(" ")
        self.date = dt[0]
        self.time = dt[1]

        # Counts of numbers slots and barcodes
        self.num_slots = len(self.barcodes)
        self.num_empty_slots = len([b for b in self.barcodes if b == EMPTY_SLOT_SYMBOL])
        self.num_unread_slots = len([b for b in self.barcodes if b == NOT_FOUND_SLOT_SYMBOL])
        self.num_valid_barcodes = self.num_slots - self.num_unread_slots - self.num_empty_slots

    @staticmethod
    def from_plate(holder_barcode, plate, image_path, holder_image_path):
        return Record(plate_type=plate.type, holder_barcode=holder_barcode, barcodes=plate.barcodes(),
                      image_path=image_path, holder_image_path=holder_image_path, geometry=plate.geometry())

    @staticmethod
    def from_string(string):
        """ Creates a scan record object from a semi-colon separated string. This is
        used when reading a stored record back from file.
        """
        items = string.strip().split(Record.ITEM_SEPARATOR)
        id = items[Record.IND_ID]
        timestamp = items[Record.IND_TIMESTAMP] #used to convert into float twice
        image = items[Record.IND_IMAGE]
        holder_image_path = items[Record.IND_HOLDER_IMAGE]
        
        plate_type = items[Record.IND_PLATE]
        all_barcodes = items[Record.IND_BARCODES].split(Record.BC_SEPARATOR)
        holder_barcode = all_barcodes[0]
        pin_barcodes = all_barcodes[1:]

        geo_class = Geometry.get_class(plate_type)
        geometry = geo_class.deserialize(items[Record.IND_GEOMETRY])

        return Record(plate_type=plate_type, holder_barcode=holder_barcode, barcodes=pin_barcodes, timestamp=timestamp,
                      image_path=image, holder_image_path=holder_image_path, id=id, geometry=geometry)

    def to_csv_string(self):
        """ Converts a scan record object into a string that can be stored in a csv file.
        """
        items = list()
        items.append(str(self.id))
        items.append(str(self._formatted_date()))
        items.append(self.holder_barcode)
        items.append(Record.BC_SEPARATOR.join(self.barcodes))
        return Record.BC_SEPARATOR.join(items)

    def to_string(self):
        """ Converts a scan record object into a string that can be stored in a file
        and retrieved later.
        """
        items = [0] * Record.NUM_RECORD_ITEMS
        items[Record.IND_ID] = str(self.id)
        items[Record.IND_TIMESTAMP] = str(self.timestamp)
        items[Record.IND_IMAGE] = self.image_path
        items[Record.IND_HOLDER_IMAGE] = self.holder_image_path
        items[Record.IND_PLATE] = self.plate_type
        items[Record.IND_BARCODES] = Record.BC_SEPARATOR.join(self._all_barcodes())
        items[Record.IND_GEOMETRY] = self.geometry.serialize()
        return Record.ITEM_SEPARATOR.join(items)

    def _all_barcodes(self):
        return [self.holder_barcode] + self.barcodes

    def get_image(self):
        image = Image.from_file(self.image_path)
        return image
    
    def get_holder_image(self):
        image = Image.from_file(self.holder_image_path)
        return image
    
    def get_marked_image(self, options):
        image = self.get_image()
        geo = self.geometry
           

        if options.image_puck.value():
            geo.draw_plate(image, Color.Blue())

        if options.image_pins.value():
            self._draw_pins(image, geo, options)

        if options.image_crop.value():
            geo.crop_image(image)

        return image



    # marking the top image
    def _draw_pins(self, image, geometry, options):
        for i, bc in enumerate(self.barcodes):
            if bc == NOT_FOUND_SLOT_SYMBOL:
                color = options.col_bad()
            elif bc == EMPTY_SLOT_SYMBOL:
                color = options.col_empty()
            else:
                color = options.col_ok()

            geometry.draw_pin_highlight(image, color, i+1)

    def _formatted_date(self):
        """ Provides a human-readable form of the datetime stamp
        """
        return datetime.datetime.fromtimestamp(self.timestamp).strftime(Record.DATE_FORMAT)


