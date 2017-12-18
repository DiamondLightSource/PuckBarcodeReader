import time, os, shutil

from dls_barcode.config.barcode_config import BarcodeConfig
from dls_barcode.data_store import Store
from dls_barcode.scan import GeometryScanner
from dls_util.image import Image
from dls_util.file import FileManager

# SHOULD BE OPEN CV 2.4.10

# Directory storing all of the test images
TEST_IMG_DIR = '../../tests/test-resources/'
CONFIG_FILE = os.path.join(TEST_IMG_DIR, "system_test_config.ini")
FILE_MANAGER = FileManager()
OPTIONS = BarcodeConfig(CONFIG_FILE, FILE_MANAGER)

# Clear store before creating a new one
store_dir = OPTIONS.store_directory.value()
wd = os.getcwd()
if os.path.isdir(store_dir):
    shutil.rmtree(store_dir)

STORE = Store(store_dir, OPTIONS.store_capacity, FILE_MANAGER)


def test_generator():
    TEST_CASES = generate_test_cases()
    for params in TEST_CASES:
        yield run_scans, params[0], params[1]


def run_scans(img_file, expected_codes):
    filepath = os.path.join(TEST_IMG_DIR, img_file)
    cv_image = Image.from_file(filepath)
    gray_image = cv_image.to_grayscale()
    results = GeometryScanner("Unipuck", [14]).scan_next_frame(gray_image, is_single_image=True)
    plate = results.plate()
    store_scan(img_file, plate, cv_image)

    correctly_read_count = 0
    slots = [plate.slot(i) for i in range(16)]
    num_found = len([s for s in slots if s.state() == s.VALID])
    assert num_found == len(expected_codes)

    for expected_code in expected_codes:
        expected_code_text = expected_code[0]
        slot = expected_code[1]

        barcode_read = plate.slot(slot).barcode_data()
        if barcode_read == expected_code_text:
            correctly_read_count += 1

    assert correctly_read_count == len(expected_codes)


def generate_test_cases():
    # Barcode data that is expected to appear in each image of the pucks
    PUCK1_CODES = [['DF150E0101', 1], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0156', 7], ['DF150E0129', 8],
                   ['DF150E0323', 9], ['DF150E0042', 10], ['DF150E0443', 12], ['DF150E0370', 14], ['DF150E0250', 16]]

    PUCK2_CODES = [['DF150E0101', 1], ['DF150E0073', 2], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0135', 5],
                   ['DF150E0342', 6], ['DF150E0156', 7], ['DF150E0129', 8], ['DF150E0323', 9], ['DF150E0042', 10],
                   ['DF150E0453', 11], ['DF150E0443', 12], ['DF150E0074', 13], ['DF150E0370', 14], ['DF150E0066', 15],
                   ['DF150E0250', 16]]

    # List of files for Puck type 1
    puck1_files = ['puck1_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 26)]
    puck1_testcases = [(file, PUCK1_CODES) for file in puck1_files]

    # List of files for Puck type 2
    puck2_files = ['puck2_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1, 5)]
    puck2_testcases = [(file, PUCK2_CODES) for file in puck2_files]

    # Create a list of test cases
    test_cases = []
    test_cases.extend(puck1_testcases)
    test_cases.extend(puck2_testcases)
    return test_cases


def store_scan(img_file, plate, pins_img):
    dummy_holder_barcode = img_file
    holder_img = pins_img.copy()
    STORE.merge_record(dummy_holder_barcode, plate, holder_img, pins_img)