#!/usr/bin/env dls-python
from dls_barcode import *
import time

# SHOULD BE OPEN CV 2.4.10

# Directory storing all of the test images
TEST_IMG_DIR = './test-images/'

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
TEST_CASES.extend(puck2_testcases)


def run_tests():
    # Run all of the test cases
    total = 0
    correct = 0
    found = 0
    start = time.clock()
    for case in TEST_CASES:
        file = case[0]
        barcodes = case[1]
        total = total + len(barcodes)

        filename = TEST_IMG_DIR + file
        cv_image = CvImage(filename)
        dms, puck = Barcode.ScanImage(cv_image)

        pass_count = 0
        for expected_code in barcodes:
            text = expected_code[0]
            slot = expected_code[1]

            result = 0
            for dm in dms:
                if dm.data == text and dm.pinSlot == slot:
                    result = 1
                    break

            pass_count = pass_count + result

        result = "pass" if pass_count == len(barcodes) else "FAIL"
        print file, "-", result, " - ", pass_count, "/", len(barcodes), " matches  (", len(dms), "found )"

        correct = correct + pass_count
        found = found + len(dms)

    end = time.clock()

    print "Summary |", end - start, "secs |", correct, "correct |", found, "found |", total, "total"


if __name__ == '__main__':
    run_tests()


