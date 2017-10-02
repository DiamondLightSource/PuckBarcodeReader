class NoNewBarcodeMessage:
    pass

class ScanErrorMessage:
    def __init__(self, content):
        self._content = content

    def content(self):
        return self._content