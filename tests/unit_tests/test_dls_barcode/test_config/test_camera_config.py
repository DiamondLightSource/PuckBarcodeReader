import unittest
from dls_barcode.config.camera_config import CameraConfig

class TestCameraConfig(unittest.TestCase):

    def test_parameters_are_initialised_correctly(self):
        # Arrange
        number = 3
        width = 100
        height = 200

        # Act
        cfg = CameraConfig(number, width, height)

        # Assert
        self.assertEqual(cfg.camera_number, number)
        self.assertEqual(cfg.width, width)
        self.assertEqual(cfg.height, height)