"""Location, retrieval and reading of Data Matrix-style barcodes.
"""
from datamatrix import DataMatrix
from image import CvImage
from align import Aligner


# testing
from reedsolo import RSDecode, ReedSolomonError
from decode import Decoder
