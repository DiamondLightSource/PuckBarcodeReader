"""Location, retrieval and reading of Data Matrix-style barcodes.
"""
from scan import Scan
from dls_barcode.plate.align import Aligner
from image import CvImage
# testing
from dls_barcode.datamatrix.reedsolo import RSDecode, ReedSolomonError
from dls_barcode.datamatrix.decode import Decoder
