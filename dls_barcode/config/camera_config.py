from dls_util.config import Config, IntConfigItem


class CameraConfig(Config):

    def __init__(self, file):
        Config.__init__(self, file)

        add = self.add

        self.puck_camera_number = add(IntConfigItem, "Puck Camera Number", default=1)
        self.puck_camera_width = add(IntConfigItem, "Puck Camera Width", default=1600)
        self.puck_camera_height = add(IntConfigItem, "Puck Camera Height", default=1200)

        self.side_camera_number = add(IntConfigItem, "Side Camera Number", default=2)
        self.side_camera_width = add(IntConfigItem, "Side Camera Width", default=1600)
        self.side_camera_height = add(IntConfigItem, "Side Camera Height", default=1200)

        self.initialize_from_file()

    def getPuckCameraConfig(self):
        return [self.puck_camera_number, self.puck_camera_width, self.puck_camera_height]

    def getSideCameraConfig(self):
        return [self.side_camera_number, self.side_camera_width, self.side_camera_height]