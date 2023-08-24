import logging
import string
from string import ascii_lowercase

from pylibdmtx.pylibdmtx import decode

from dls_util.image.image import Image

from .locate import Locator

# We predict the location of the center of each square (pixel/bit) in the datamatrix based on the
# size and location of the finder pattern, but this can sometimes be slightly off. If the initial
# reading doesn't produce sensible results, we try to offset the estimated location of the squares
# and try again.
wiggle_offsets = [[0, 0]]


class BarcodeReadNotPerformedException(Exception):
    pass


class BarcodeReadAlreadyPerformedException(Exception):
    pass


class DataMatrix:
    """ Representation of a DataMatrix and its location in an image.
    """
    DEFAULT_SIZE = 14
    DEFAULT_SIDE_SIZES = [12, 14]
    # allow only capitol letters, digits and dash in the decoded string
    ALLOWED_CHARS = set(string.ascii_uppercase + string.ascii_lowercase + string.digits + '-' + '_')

    def __init__(self, finder_pattern):
        """ Initialize the DataMatrix object with its finder pattern location in an image. To actually
        interpret the DataMatrix, the perform_read() function must be called, which will attempt to read
        the DM from the supplied image.

        The matrix size is the width/height (in modules) of the Data matrix (including +2 for the edges).
        The message length is the number of data bytes in the encoded message (i.e. not including the
        error correction bytes).
        """
        self._finder_pattern = finder_pattern
        self._matrix_sizes = [self.DEFAULT_SIZE]

        self._data = None
        self._error_message = ""
        self._read_ok = False
        self._damaged_symbol = False
        self._is_read_performed = False
        self.log = logging.getLogger(".".join([__name__]))

    def set_matrix_sizes(self, matrix_sizes):
        self._matrix_sizes = [int(v) for v in matrix_sizes]

    def perform_read(self, image, force_read=False):
        """ Attempt to read the DataMatrix from the image supplied in the constructor at the position
        given by the finder pattern. This is not performed automatically upon construction because the
        read operation is relatively expensive and might not always be needed.
        """
        if not self._is_read_performed or force_read:
            # Read the data contained in the barcode from the image
            sub, _ = image.sub_image(self.center(), 1.2*self.radius())
            self._read(sub.img)
            self._is_read_performed = True

    def is_read(self):
        """ True if the read operation has been performed (whether successful or not) """
        return self._is_read_performed

    def is_valid(self):
        """ True if the data matrix was read successfully. """
        if not self._is_read_performed:
            self.log.debug("data matrix not read successfully")
            raise BarcodeReadNotPerformedException()

        return self._read_ok

    def is_unreadable(self):
        """ True if the data matrix could not be decoded (because of damage to the symbol). """
        if not self._is_read_performed:
            self.log.debug("data matrix not read successfully")
            raise BarcodeReadNotPerformedException()

        return self._damaged_symbol

    def data(self):
        """ String representation of the barcode data. """
        if not self._is_read_performed:
            self.log.debug("data matrix not read successfully")
            raise BarcodeReadNotPerformedException()

        if self._read_ok:
            return self._data
        else:
            return ''
    
    def bounds(self):
        """ A circle which bounds the data matrix (center, radius). """
        return self._finder_pattern.bounds()

    def center(self):
        """ The center position (x,y) of the DataMatrix finder pattern. """
        return self._finder_pattern.center

    def radius(self):
        """ The radius (center-to-corner distance) of the DataMatrix finder pattern. """
        return self._finder_pattern.radius
        
    def _read(self, gray_image):
        """ From the supplied grayscale image, attempt to read the barcode at the location
        given by the datamatrix finder pattern.
        """
        try:
            result = decode(gray_image, max_count = 1)
            if len(result) > 0:
                d = result[0].data
                decoded = d.decode('UTF-8')
                if self._contains_allowed_chars_only(decoded):
                    new_line_removed = decoded.replace("\n","")
                    self._data = new_line_removed
                    self._read_ok = True
                    self._error_message = ""
                else:
                    self._read_ok = False
            else:
                self._read_ok = False
                #cv2.imshow("Erode", gray_image)
                #cv2.waitKey(0) 
        except(Exception) as ex:
            self._read_ok = False
            self._error_message = str(ex)

        self._damaged_symbol = not self._read_ok
        
    def draw(self, img, color):
        """ Draw the lines of the finder pattern on the specified image. """
        fp = self._finder_pattern
        img.draw_line(fp.c1, fp.c2, color)
        img.draw_line(fp.c1, fp.c3, color)

    def _contains_allowed_chars_only(self, text):
        return (set(text)).issubset(self.ALLOWED_CHARS)

    @staticmethod
    def locate_all_barcodes_in_image(grayscale_img, matrix_sizes=[DEFAULT_SIZE]):
        """ Searches the image for all datamatrix finder patterns
        """
        locator = Locator()
        finder_patterns = locator.locate_shallow(grayscale_img)
        unread_barcodes = DataMatrix._fps_to_barcodes(finder_patterns, matrix_sizes)
        return unread_barcodes

    @staticmethod
    def locate_all_barcodes_in_image_deep(grayscale_img, matrix_sizes=[DEFAULT_SIDE_SIZES]):
        """ Searches the image for all datamatrix finder patterns
        """
        # TODO: deep scan is more likely to find some false finder patterns. Filter these out
        locator = Locator()
        locator.set_median_radius_tolerance(0.2)
        finder_patterns = locator.locate_deep(grayscale_img, expected_radius=None, filter_overlap=True)
        unread_barcodes = DataMatrix._fps_to_barcodes(finder_patterns, matrix_sizes)
        return unread_barcodes

    @staticmethod
    def _fps_to_barcodes(finder_patterns, matrix_sizes):
        unread_barcodes = [DataMatrix(fp) for fp in finder_patterns]
        for bc in unread_barcodes:
            bc.set_matrix_sizes(matrix_sizes)
        return list(unread_barcodes)
