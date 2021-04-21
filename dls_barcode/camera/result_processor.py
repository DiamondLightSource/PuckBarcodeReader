
from dls_util import Beeper
from .plate_overlay import PlateOverlay
from .scanner_message import NoNewBarcodeMessage, NoNewPuckBarcodeMessage
class ResultPorcessor:

    def __init__(self, result, config):
        self._config = config
        self._result = result
        self._plate = None 

    def print_summary(self):
        if self._config.console_frame.value():
            self._result.print_summary()

    def set_result_palte(self):
        self._plate = self._result.plate()

    def get_plate(self):
        return self._plate

    def get_overlay(self):
       
        self._plate_beep(self._plate, self._config.scan_beep.value())
        return PlateOverlay(self._plate, self._config)
   
    def get_message(self):
            if self._result.geometry() is not None:
                return(NoNewBarcodeMessage()) #important used in the message logic
            else:
                return(NoNewPuckBarcodeMessage())
    
    def result_success(self):
        return self._result.success()

    def result_has_any_valid_barcodes(self):
        return self._result.any_valid_barcodes()

    def result_has_any_new_barcode(self):
        return self._result.any_new_barcodes()

    def result_error(self):
        return self._result.error() is not None 

    def get_result_error(self):
        return self._result.error()

    def _plate_beep(self, plate, do_beep):
        if not do_beep:
            return

        empty_fraction = (self._plate.num_slots - self._plate.num_valid_barcodes()) / self._plate.num_slots
        frequency = int(10000 * empty_fraction + 37)
        duration = 200
        Beeper.beep(frequency, duration)





    




    def _plate_beep(self, plate, do_beep):
        if not do_beep:
            return

        empty_fraction = (plate.num_slots - plate.num_valid_barcodes()) / plate.num_slots
        frequency = int(10000 * empty_fraction + 37)
        duration = 200
        Beeper.beep(frequency, duration)