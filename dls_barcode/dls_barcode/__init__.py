"""Location, retrieval and reading of Data Matrix-style barcodes.
"""
from barcode import Barcode
from dls_barcode.puck.align import Aligner
from image import CvImage
# testing
from dls_barcode.datamatrix.reedsolo import RSDecode, ReedSolomonError
from dls_barcode.datamatrix.decode import Decoder
