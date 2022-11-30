import os, shutil

from mock import MagicMock

from dls_barcode.config.barcode_config import BarcodeConfig
from dls_barcode.data_store import Store
from dls_barcode.data_store.store_writer import StoreWriter
from dls_barcode.scan import OpenScanner
from dls_util.image import Image
from dls_util.file import FileManager
from dls_util.cv.frame import Frame
from pylibdmtx.pylibdmtx import decode
import cv2


class TestOpensScan():

    # SHOULD BE OPEN CV 2.4.10

    # Directory storing all of the test images
    TEST_IMG_DIR = 'tests/test-resources/new_side'
    CONFIG_FILE = os.path.join(TEST_IMG_DIR, "system_test_config.ini")
    FILE_MANAGER = FileManager()
    OPTIONS = BarcodeConfig(CONFIG_FILE, FILE_MANAGER)

    # Clear store before creating a new one
    store_dir = OPTIONS.store_directory
    if os.path.isdir(store_dir.value()):
        shutil.rmtree(store_dir.value())

    comms_manger = StoreWriter(OPTIONS.get_store_directory(), "store")
    STORE = Store(comms_manger, MagicMock())


    def test_generator(self):
        TEST_CASES = self.generate_test_cases()
        for params in TEST_CASES:
            self.run_scans(params[0], params[1])


    def run_scans(self, img_file, expected_code):
        filepath = os.path.join(self.TEST_IMG_DIR, img_file)
        cv_image = Image.from_file(filepath)
        f = Frame(None)
        f._image = cv_image
        result = OpenScanner([12,14]).scan_next_frame(f, is_single_image=True)
        barcode = result._barcodes[0].data()
        assert barcode == expected_code
        


    def generate_test_cases(self):
        # Barcode data that is expected to appear in each image of the pucks
        side_code_old ='DF-039'

        side_code_new1 ='ASAP-01'
        
        side_code_new2 ='ASAP-02'

        # List of files for Puck type 1
        side_testcases = [('new2.jpg', side_code_new2),('new1.png', side_code_new1),('old_side.png', side_code_old)]

        # Create a list of test cases
        test_cases = []
        test_cases.extend(side_testcases)
        return test_cases

