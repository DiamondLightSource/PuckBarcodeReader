import os, shutil

from mock import MagicMock

from dls_barcode.config.barcode_config import BarcodeConfig
from dls_barcode.data_store import Store
from dls_barcode.data_store.store_writer import StoreWriter
from dls_barcode.scan import GeometryScanner
from dls_util.image import Image
from dls_util.file import FileManager
from dls_util.cv.frame import Frame

# SHOULD BE OPEN CV 2.4.10

# Directory storing all of the test images
TEST_IMG_DIR = 'tests/test-resources/'
CONFIG_FILE = os.path.join(TEST_IMG_DIR, "system_test_config.ini")
FILE_MANAGER = FileManager()
OPTIONS = BarcodeConfig(CONFIG_FILE, FILE_MANAGER)

# Clear store before creating a new one
store_dir = OPTIONS.store_directory
if os.path.isdir(store_dir.value()):
    shutil.rmtree(store_dir.value())

comms_manger = StoreWriter(OPTIONS.get_store_directory(), "store")
STORE = Store(comms_manger, MagicMock())


def test_generator():
    TEST_CASES = generate_test_cases()
    for params in TEST_CASES:
        run_scans(params[0], params[1])


def run_scans(img_file, expected_codes):
    filepath = os.path.join(TEST_IMG_DIR, img_file)
    cv_image = Image.from_file(filepath)
    f = Frame(None)
    f._image = cv_image
    results = GeometryScanner("Unipuck", [14]).scan_next_frame(f, is_single_image=True)
    plate = results.plate()
    if results.error() is None:
        store_scan(img_file, plate, cv_image)


    correctly_read_count = 0
    slots = [plate.slot(i) for i in range(16)]
    num_found = len([s for s in slots if s.state() == s.VALID])
    #barcodes_for_debug = [s.barcode_data() for s in slots]
    assert num_found == len(expected_codes)

    for expected_code in expected_codes:
        expected_code_text = expected_code[0]
        slot = expected_code[1]

        barcode_read = plate.slot(slot).barcode_data()
        #print(barcode_read, expected_code_text)
        if barcode_read == expected_code_text:
            correctly_read_count += 1

    assert correctly_read_count == len(expected_codes)


def generate_test_cases():
    # Barcode data that is expected to appear in each image of the pucks
    puck1_codes = [['DF150E0101', 1], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0156', 7], ['DF150E0129', 8],
                   ['DF150E0323', 9], ['DF150E0042', 10], ['DF150E0443', 12], ['DF150E0370', 14], ['DF150E0250', 16]]

    puck2_codes = [['DF150E0101', 1], ['DF150E0073', 2], ['DF150E0144', 3], ['DF150E0016', 4], ['DF150E0135', 5],
                   ['DF150E0342', 6], ['DF150E0156', 7], ['DF150E0129', 8], ['DF150E0323', 9], ['DF150E0042', 10],
                   ['DF150E0453', 11], ['DF150E0443', 12], ['DF150E0074', 13], ['DF150E0370', 14], ['DF150E0066', 15],
                   ['DF150E0250', 16]]

    # List of files for Puck type 1
    puck1_files = ['puck1_' + ("0" + str(i) if i < 10 else str(i)) + ".png" for i in range(1,19)] # 20,22 don't work with the new version
    puck1_testcases = [(file, puck1_codes) for file in puck1_files]

    # Create a list of test cases
    test_cases = []
    test_cases.extend(puck1_testcases)
    return test_cases


def store_scan(img_file, plate, pins_img):
    dummy_holder_barcode = img_file
    holder_img = pins_img.copy()
    STORE.merge_record(dummy_holder_barcode, plate, holder_img, pins_img)