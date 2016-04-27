from __future__ import division

import cv2
import math
import numpy as np
from scipy.optimize import fmin
from dls_barcode import Image, Transform
from dls_barcode.datamatrix import DataMatrix
from dls_barcode.datamatrix.finder_pattern import FinderPattern
from dls_barcode.datamatrix.locate_square import SquareLocator


IMG_ROOT_DIR = '../test-output/bad_barcodes/'
OUT_DIR = IMG_ROOT_DIR + 'algorithm_test/'



# ----------------------------------
# Prepare
# ----------------------------------
barcode_size = 76
rotation = 0

original = Image(IMG_ROOT_DIR + 't12_76.png').to_grayscale()


locator = SquareLocator()
locator.DEBUG = True
fp = locator.locate(original, barcode_size)


w = 0.25
wiggle_offsets = [[0,0], [w, w],[-w,-w],[w,-w],[-w,w]]
barcode = DataMatrix(fp, original, wiggle_offsets)
print(barcode.data())



# Old locator method
fps = DataMatrix.LocateAllBarcodesInImage(original)
fp_img = original.to_alpha()
for fp in fps:
    fp.draw_to_image(fp_img)
    fp_img.rescale(4).popup()
    barcode = DataMatrix(fp, original, wiggle_offsets)
    print(barcode.data())
