import time

from dls_barcode.scan import SlotScanner

# TODO: sort out the doc string
class ScannerWorker:

    def run(self, terminate_queue):
        pass
        # while kill_queue.empty():
        #
        #
        #
        # last_plate_time = time.time()
        #
        # SlotScanner.DEBUG = options.slot_images.value()
        # SlotScanner.DEBUG_DIR = options.slot_image_directory.value()
        #
        # if ("Side" in camera_config[0]._tag):
        #     # Side camera
        #     plate_type = "None"
        #     barcode_sizes = DataMatrix.DEFAULT_SIDE_SIZES
        # else:
        #     # Top camera
        #     plate_type = options.plate_type.value()
        #     barcode_sizes = [options.top_barcode_size.value()]
        #
        # if plate_type == "None":
        #     scanner = OpenScanner(barcode_sizes)
        # else:
        #     scanner = GeometryScanner(plate_type, barcode_sizes)