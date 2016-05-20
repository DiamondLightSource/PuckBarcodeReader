from __future__ import division

import os
import time
from dls_barcode import Image
from dls_barcode.datamatrix import DataMatrix
from dls_barcode.datamatrix.locate_square import SquareLocator


class SquareTest:
    """ Put test cases (images of individual barcodes) in a subdirectory under ROOT_DIR. The first
    two characters of the file name of each image should be the estimated side length in pixels
    (01-99) of the barcode.

    The name of the subdirectory should be passed to the constructor as the 'case' argument.
    """
    # Prepare wiggles for reading
    w = 0.25
    WIGGLES = [[0, 0], [w, w], [-w, -w], [w, -w], [-w, w]]

    ROOT_DIR = '../test-output/square_test/'

    def __init__(self, case, debug):
        self.case = case
        self.directory = self.ROOT_DIR + case + "/"

        self.locator = SquareLocator()
        self.locator.DEBUG = debug

        # Counters
        self.count_success = 0
        self.count_iters = 0

    def process_all(self):
        print("-------- " + self.case + " -------")
        # Get list of test case files
        paths = [os.path.join(self.directory, o) for o in os.listdir(self.directory)]
        good_files = [p for p in paths if os.path.isfile(p)]
        count_total = len(good_files)

        start_time = time.time()
        for filepath in good_files:
            self._process_file(filepath)

        total_time = time.time()-start_time

        if count_total > 0:
            print("SUCCESSFUL READS - {} / {}".format(self.count_success, count_total))
            print("TOTAL ITERATIONS = {} ({:.1f} each)".format(self.count_iters, self.count_iters/count_total))
            print("TIME - {:.2f} ({:.2f} each)".format(total_time, total_time/count_total))

    def _process_file(self, filepath):
        filename = filepath.split("/")[-1]

        barcode_size = int(filename[:2])

        color = Image(filepath).to_alpha()
        gray = color.to_grayscale()

        fp = self.locator.locate(gray, barcode_size)
        barcode = DataMatrix(fp, gray)
        barcode.perform_read(self.WIGGLES)

        iters = self.locator.count
        self.count_iters += iters

        print("{} - {} - {}".format(filename, iters, barcode.data()))
        if barcode.is_valid():
            self.count_success += 1

        # fp.draw_to_image(color)
        # color.rescale(2).popup()


def main():
    good_tester = SquareTest("good", False)
    good_tester.process_all()

    bad_tester = SquareTest("bad", False)
    bad_tester.process_all()


if __name__ == '__main__':
    main()


