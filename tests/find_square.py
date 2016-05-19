from __future__ import division

import os
from dls_barcode import Image
from dls_barcode.datamatrix import DataMatrix, Locator
from dls_barcode.datamatrix.locate_square import SquareLocator


IMG_ROOT_DIR = '../test-output/square_test/good/'
OUT_DIR = IMG_ROOT_DIR + 'algorithm_test/'


# Get list of test case files
paths = [os.path.join(IMG_ROOT_DIR, o) for o in os.listdir(IMG_ROOT_DIR)]
good_files = [p for p in paths if os.path.isfile(p)]

# Prepare locator object
locator = SquareLocator()
locator.DEBUG = False

# Prepare wiggles for reading
w = 0.25
wiggle_offsets = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]


good_total = len(good_files)
good_success = 0
good_iter_count = 0


for filepath in good_files:
    filename = filepath.split("/")[-1]

    barcode_size = int(filename[:2])
    rotation = 0

    color = Image(filepath).to_alpha()
    gray = color.to_grayscale()

    fp = locator.locate(gray, barcode_size)
    barcode = DataMatrix(fp, gray)
    barcode.perform_read(wiggle_offsets)

    iters = locator.count
    good_iter_count += iters
    print("{} - {} - {}".format(filename, iters, barcode.data()))

    if barcode.is_valid():
        good_success += 1

    fp.draw_to_image(color)
    #color.rescale(2).popup()


print("GOOD READS - {} / {}".format(good_success, good_total))
print("TOTAL ITERATIONS = {} ({} per)".format(good_iter_count, good_iter_count/good_total))