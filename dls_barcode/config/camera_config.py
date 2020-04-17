class CameraConfig:
    """Class that groups the config items of a single camera"""

    def __init__(self, camera_number, width, height):
        self.camera_number = camera_number
        self.width = width
        self.height = height

    def get_number_item_value(self):
        return self.camera_number.value()

    def get_width_item_value(self):
        return self.width.value()

    def get_height_item_value(self):
        return self.height.value()

    def set_number_item_value(self, number):
        self.camera_number.set(number)

    def set_width_item_value(self, width):
        self.width.set(width)

    def set_height_item_value(self, height):
        self.height.set(height)



