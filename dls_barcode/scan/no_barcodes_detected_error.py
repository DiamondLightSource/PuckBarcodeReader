class NoBarcodesDetectedError(Exception):
    def __init__(self):
        super(NoBarcodesDetectedError, self).__init__("No barcode detected")
