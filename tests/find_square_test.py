#!/usr/bin/env dls-python
from dls_barcode import Image, Scanner, Store, Record
from dls_barcode.datamatrix import DataMatrix
from dls_barcode.datamatrix.locate_square import SquareLocator
import time

import numpy as np
import math

# SHOULD BE OPEN CV 2.4.10

# Directory storing all of the test images
TEST_IMG_DIR = './test-resources/'

# Barcode data that is expected to appear in each image of the pucks
PUCK1_CODES = [['DF150E0101', 1], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0156', 7], ['DF150E0129', 8],
               ['DF150E0323', 9], ['DF150E0042', 10], ['DF150E0443', 12], ['DF150E0370', 14], ['DF150E0250', 16]]

PUCK2_CODES = [['DF150E0101', 1], ['DF150E0073', 2], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0135', 5],
               ['DF150E0342', 6], ['DF150E0156', 7], ['DF150E0129', 8], ['DF150E0323', 9], ['DF150E0042', 10],
               ['DF150E0453', 11], ['DF150E0443', 12], ['DF150E0074', 13], ['DF150E0370', 14], ['DF150E0066', 15],
               ['DF150E0250', 16]]

# List of files for Puck type 1
puck1_files = ['puck1_'+ ("0"+str(i) if i <10 else str(i)) +".png" for i in range(1,26)]
puck1_testcases = [(file, PUCK1_CODES) for file in puck1_files]

# List of files for Puck type 2
puck2_files = ['puck2_'+ ("0"+str(i) if i <10 else str(i)) +".png" for i in range(1,5)]
puck2_testcases = [(file, PUCK2_CODES) for file in puck2_files]

# Create a list of test cases
TEST_CASES = []
TEST_CASES.extend(puck1_testcases)
#TEST_CASES.extend(puck2_testcases)

TEST_OUTPUT_PATH = '../test-output/'
STORE_FILE = TEST_OUTPUT_PATH + 'store.txt'
STORE_IMAGE_PATH = TEST_OUTPUT_PATH + 'img_store/'
STORE = Store.from_file(STORE_FILE)

def store_scan(plate, cvimg):
    plate.draw_plate(cvimg, Image.BLUE)
    plate.draw_pins(cvimg)
    plate.crop_image(cvimg)
    STORE.add_record(plate.type, plate.barcodes(), cvimg)


def run_tests():

    # Run all of the test cases
    total = 0
    correct = 0
    found = 0
    start = time.clock()
    for case in TEST_CASES:
        file = case[0]
        expected_codes = case[1]
        total += len(expected_codes)

        filename = TEST_IMG_DIR + file
        cv_image = Image(filename)
        gray_image = cv_image.to_grayscale()

        finder_patterns = DataMatrix.LocateAllBarcodesInImage(gray_image)
        fp_radius = np.mean([fp.radius for fp in finder_patterns])

        w = 0.5
        wiggle_offsets = [[0,0], [w, w],[-w,-w],[w,-w],[-w,w]]

        locator = SquareLocator()
        locator.DEBUG = True
        for fp in finder_patterns:
            img, _ = gray_image.sub_image(fp.center, fp.radius * 2)

            side_length = fp.radius / math.sqrt(2) * 2

            new_fp = locator.locate(img, side_length)

            #fp_img = img.to_alpha()
            #new_fp.draw_to_image(fp_img)
            #fp_img.rescale(4).popup()

            sub_fp = DataMatrix.LocateAllBarcodesInImage(img)[0]
            #sub_fp.draw_to_image(fp_img)

            print(DataMatrix(new_fp, img, wiggle_offsets).data())
            #fp_img.rescale(4).popup()


    end = time.clock()
    print("Summary | {0} secs | {1} correct | {2} found | {3} total".format(end-start, correct,found,total))


if __name__ == '__main__':
    run_tests()


