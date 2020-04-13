class CameraConfig:
    """Class that groups the config items of a single camera"""

    def __init__(self, camera_number, width, height):
        self.camera_number = camera_number
        self.width = width
        self.height = height

    def get_number(self):
        return self.camera_number.value()

    def get_width(self):
        return self.width.value()

    def get_height(self):
        return self.height.value()

    def set_number(self, number):
        self.camera_number.set(number)

    def set_width(self, width):
        self.width.set(width)

    def set_height(self, height):
        self.height.set(height)



