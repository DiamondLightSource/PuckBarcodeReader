class NoNewBarcodeMessage:
    pass


class NoNewPuckBarcodeMessage:
    pass


class ScanErrorMessage:
    def __init__(self, content):
        self._content = content

    def content(self):
        return self._content


class CameraErrorMessage:
    def __init__(self, content):
        self._content = content

    def content(self):
        return self._content
