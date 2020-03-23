import os, shutil

import cv2
import numpy as np
from mock import MagicMock

from dls_barcode.config.barcode_config import BarcodeConfig
from dls_barcode.data_store import Store
from dls_barcode.data_store.store_writer import StoreWriter
from dls_barcode.geometry.unipuck import Unipuck
from dls_barcode.scan import GeometryScanner
from dls_util import Color
from dls_util.image import Image
from dls_util.file import FileManager

# SHOULD BE OPEN CV 2.4.10

# Directory storing all of the test images
from dls_util.shape import Point

TEST_IMG_DIR = 'tests/test-resources/blue_stand/'
CONFIG_FILE = os.path.join(TEST_IMG_DIR, "system_test_config.ini")
FILE_MANAGER = FileManager()
OPTIONS = BarcodeConfig(CONFIG_FILE, FILE_MANAGER)

# Clear store before creating a new one
store_dir = OPTIONS.store_directory
if os.path.isdir(store_dir.value()):
    shutil.rmtree(store_dir.value())
comms_manger = StoreWriter(OPTIONS.get_store_directory(), "store")
STORE = Store(comms_manger, MagicMock)

def test_generator():
    TEST_CASES = generate_test_cases()
    for params in TEST_CASES:
        yield run_scans, params[0], params[1]

def run_scans(img_file, expected_codes):
    filepath = os.path.join(TEST_IMG_DIR, img_file)
    print(img_file)
    cv_image = Image.from_file(filepath)
    gray_image = cv_image.to_grayscale()
    results = GeometryScanner("Unipuck", [14]).scan_next_frame(gray_image, is_single_image=True)
    plate = results.plate()
    if plate != None:
        for expected_code in expected_codes:
            expected_code_text = expected_code[0] #text
            slot_number = expected_code[1] #number
            slot = plate.slot(slot_number)
            read_code_text = slot.barcode_data()
            print(slot_number, read_code_text, expected_code_text)
            if slot.state() == slot.VALID:
                assert read_code_text == expected_code_text


def generate_test_cases():
    # Barcode data that is expected to appear in each image of the pucks
    puck1_codes = [['DF150E0101', 1], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0156', 7], ['DF150E0129', 8],
                   ['DF150E0323', 9], ['DF150E0042', 10], ['DF150E0443', 12], ['DF150E0370', 14], ['DF150E0250', 16]]

    puck2_codes = [['DF075C0421', 1], ['DF150E0454', 2], ['DF075C0118', 3], ['DF075C0823', 4], ['DF150E0844', 5],
                   ['DF075C1287', 6], ['DF075C1191', 7], ['DF075C0600', 8], ['DF075C1038', 9], ['DF075C1363', 10],
                   ['DF075C1298', 11], ['DF075C1339', 12], ['DF075C0932', 13], ['DF075C1202', 14], ['DF075C0711', 15],
                   ['DF075C0595', 16]]

    puck3_codes = [['DF075C0843', 3], ['DF075C1005', 5], ['DF075C1099', 7]]

    puck4_codes = [['DF150E0853', 1], ['DF150E1004', 2], ['DF150E0723', 3], ['DF150E0284', 4], ['DF150E0792',5],
                   ['DF150E0834', 6], ['DF150E0212', 7], ['DF150E0564', 8], ['DF150E0457', 9], ['DF150E0717', 10],
                   ['DF150E0714', 11], ['DF150E0523', 12],['DF150E0231', 13], ['DF150E0200', 14], ['DF150E0102', 15],
                   ['DF150E0964', 16]]

    puck5_codes = [['DF150E0870', 1], ['DF150E1029', 2], ['DF150E1022', 3], ['DF150E0342', 4], ['DF150E0708', 5],
                   ['DF150E0806', 6], ['DF150E0678', 7], ['DF150E0721', 8], ['DF150E0816', 9], ['DF150E0660', 10],
                   ['DF075E0276', 11], ['DF150E0414', 12], ['DF150E0166', 13], ['DF150E1008', 14], ['DF150E1050', 15],
                   ['DF150E0806', 16]]

    # List of files for Puck type 1
    puck1_files = ['puck1_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 5)]
    puck1_testcases = [(file, puck1_codes) for file in puck1_files]

    # List of files for Puck type 2
    puck2_files = ['puck2_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 2)]
    puck2_testcases = [(file, puck2_codes) for file in puck2_files]

    # List of files for Puck type 2
    puck3_files = ['puck3_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 8)]
    puck3_testcases = [(file, puck3_codes) for file in puck3_files]

    # List of files for Puck type 2
    puck4_files = ['puck4_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 6)]
    puck4_testcases = [(file, puck4_codes) for file in puck4_files]

    puck5_files = ['puck5_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 2)]
    puck5_testcases = [(file, puck5_codes) for file in puck5_files]


    # Create a list of test cases
    test_cases = []
    #test_cases.extend(puck1_testcases)
    #test_cases.extend(puck2_testcases)
    #test_cases.extend(puck3_testcases)
    #test_cases.extend(puck4_testcases)
    test_cases.extend(puck5_testcases)
    return test_cases


def store_scan(img_file, plate, pins_img):
    dummy_holder_barcode = img_file
    holder_img = pins_img.copy()
    STORE.merge_record(dummy_holder_barcode, plate, holder_img, pins_img)