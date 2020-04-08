class Camera:

    def __init__(self, camera_number, width, height):
        self._camera_number = camera_number
        self._width = width
        self._height = height

    def get_camera_number(self):
        return self._camera_number

    def get_camera_width(self):
        return self._width

    def get_camera_height(self):
        return self._height

