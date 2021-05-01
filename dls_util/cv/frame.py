from dls_util.image import Image

class Frame:
    
    def __init__(self, original_frame):
       self._frame = original_frame
       self._image =  Image(self._frame)
       
    def get_copy(self):
        return self._frame.copy()
    
    def get_frame(self):
        return self._frame
    
    def frame_to_image(self):
        return self._image

    def get_image(self):
        return self._image
    
    def convert_to_gray(self):
        return self._image.to_grayscale()
    

       