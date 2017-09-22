import unittest

from dls_barcode.camera.camera_position import CameraPosition
from dls_barcode.camera.capture_command import CaptureCommand
from dls_barcode.camera.stream_action import StreamAction

class TestCaptureCommand(unittest.TestCase):
    def test_stop_command_has_no_camera_position(self):
        # Arrange
        action = StreamAction.STOP

        # Act
        cmd = CaptureCommand(action)

        # Assert
        self.assertEqual(cmd.get_action(), action)
        self.assertIsNone(cmd.get_camera_position())

    def test_stop_command_ignores_camera_position(self):
        # Arrange
        action = StreamAction.STOP

        # Act
        cmd = CaptureCommand(action, CameraPosition.SIDE)

        # Assert
        self.assertEqual(cmd.get_action(), action)
        self.assertIsNone(cmd.get_camera_position())

    def test_start_command_initialised_correctly(self):
        # Arrange
        positions = [CameraPosition.TOP, CameraPosition.SIDE]
        action = StreamAction.START

        for pos in positions:
            # Act
            cmd = CaptureCommand(action, pos)

            # Assert
            self.assertEqual(cmd.get_action(), action)
            self.assertEqual(cmd.get_camera_position(), pos)

    def test_start_command_must_specify_a_camera_position(self):
        # Act/Assert
        with self.assertRaises(ValueError):
            CaptureCommand(StreamAction.START)
