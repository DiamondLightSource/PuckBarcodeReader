from dls_util.image import Image
class FrameProcessor:

    def __init__(self, frame, scanner):
        self._frame = frame
        self._scanner = scanner
        self._gray_frame = None
        self._image = None

    def convert_to_gray(self):
        self._image =  Image(self._frame)
        self._gray_frame =self._image.to_grayscale()

    def get_image(self):
        return self._image
    
    def scan_frame(self):
        return self._scanner.scan_next_frame(self._gray_frame)