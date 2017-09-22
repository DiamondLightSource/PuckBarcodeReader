import unittest
from mock import MagicMock

import time
from dls_barcode.camera import CameraSwitch
from dls_barcode.camera.camera_position import CameraPosition

START = "start"
STOP = "stop"
TIMEOUT = 0.5

class TestCameraSwitch(unittest.TestCase):

    def setUp(self):
        self._mock_scanner = MagicMock()
        self._mock_config = MagicMock()
        self._mock_camera_config = MagicMock()

        self._list_of_calls = []

    def test_a_new_switch_flags_no_top_scan_timeout(self):
        # Act
        switch = self._create_switch()

        # Assert
        self.assertFalse(switch.is_top_scan_timeout())

    def test_a_new_switch_points_to_the_side(self):
        # Act
        switch = self._create_switch()

        # Assert
        self.assertTrue(switch.is_side())

    def test_given_a_new_switch_then_we_can_stop_the_stream(self):
        # Arrange
        switch = self._create_switch()

        # Act
        switch.stop_live_capture()

        # Assert
        self._mock_scanner.stop_scan.assert_called_once()

    def test_given_a_new_switch_when_stopping_the_stream_then_there_is_no_top_scan_timeout(self):
        # Arrange
        switch = self._create_switch()

        # Act
        switch.stop_live_capture()

        # Assert
        self.assertFalse(switch.is_top_scan_timeout())

    def test_when_restarting_capture_from_side_then_stream_is_stopped_before_being_started(self):
        # Arrange
        self._mock_scanner.start_scan.side_effect = self._stream_start_side_effect
        self._mock_scanner.stop_scan.side_effect = self._stream_stop_side_effect
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_side()

        # Assert
        self._mock_scanner.stop_scan.assert_called_once()
        self._mock_scanner.start_scan.assert_called_once()
        # Check they were called in the right order
        self.assertListEqual(self._list_of_calls, [STOP, START])

    def test_when_restarting_capture_from_side_then_switch_points_to_side(self):
        # Arrange
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_side()

        # Assert
        self.assertTrue(switch.is_side())

    def test_when_restarting_capture_from_side_then_correct_configs_are_used(self):
        # Arrange
        mock_side_camera_config = MagicMock()
        self._mock_camera_config.getSideCameraConfig.return_value = mock_side_camera_config
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_side()

        # Assert
        self._mock_scanner.start_scan.assert_called_once_with(CameraPosition.SIDE, self._mock_config)

    def test_when_restarting_capture_from_top_then_stream_is_stopped_before_being_started(self):
        # Arrange
        self._mock_scanner.start_scan.side_effect = self._stream_start_side_effect
        self._mock_scanner.stop_scan.side_effect = self._stream_stop_side_effect
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_top()

        # Assert
        self._mock_scanner.stop_scan.assert_called_once()
        self._mock_scanner.start_scan.assert_called_once()
        # Check they were called in the right order
        self.assertListEqual(self._list_of_calls, [STOP, START])

    def test_when_restarting_capture_from_top_then_switch_does_not_point_to_side(self):
        # Arrange
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_top()

        # Assert
        self.assertFalse(switch.is_side())

    def test_when_restarting_capture_from_top_then_correct_configs_are_used(self):
        # Arrange
        mock_top_camera_config = MagicMock()
        self._mock_camera_config.getPuckCameraConfig.return_value = mock_top_camera_config
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_top()

        # Assert
        self._mock_scanner.start_scan.assert_called_once_with(CameraPosition.TOP, self._mock_config)

    def test_when_restarting_capture_from_top_then_timeout_is_checked(self):
        # Arrange
        timeout = TIMEOUT # s
        self._mock_config.top_camera_timeout.value.return_value = timeout
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_top()

        # Assert
        self.assertFalse(switch.is_top_scan_timeout())
        time.sleep(timeout)
        self.assertTrue(switch.is_top_scan_timeout())

    def test_when_restarting_capture_from_side_then_timeout_is_not_checked(self):
        # Arrange
        timeout = TIMEOUT # s
        self._mock_config.top_camera_timeout.value.return_value = timeout
        switch = self._create_switch()

        # Act
        switch.restart_live_capture_from_side()

        # Assert
        self.assertFalse(switch.is_top_scan_timeout())
        time.sleep(timeout)
        self.assertFalse(switch.is_top_scan_timeout())

    def test_given_capture_started_from_top_when_capture_is_stopped_then_timeout_is_not_checked(self):
        # Arrange
        timeout = TIMEOUT # s
        self._mock_config.top_camera_timeout.value.return_value = timeout
        switch = self._create_switch()
        switch.restart_live_capture_from_top()

        # Act
        switch.stop_live_capture()

        # Assert
        time.sleep(timeout)
        self.assertFalse(switch.is_top_scan_timeout())

    def _create_switch(self):
        return CameraSwitch(self._mock_scanner, self._mock_config)

    def _stream_start_side_effect(self, unused1, unused2):
        self._list_of_calls.append(START)

    def _stream_stop_side_effect(self):
        self._list_of_calls.append(STOP)


