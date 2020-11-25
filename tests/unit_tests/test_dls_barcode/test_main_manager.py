import unittest

import time
from mock import MagicMock

from dls_barcode.main_manager import MainManager


class TestMainManager(unittest.TestCase):

    def setUp(self):
        self._ui = MagicMock()
        self._config = MagicMock()
        self._process_logger = MagicMock()
        self._list_of_calls = []
        #initialise manager
        self._manager = MainManager(self._ui, self._config, self._process_logger)
        self._manager._camera_switch = MagicMock()
        self._manager._camera_scanner = MagicMock()

    def test_camera_capture_not_alive_when_cameras_scanner_and_switch_none(self):
        self._manager._camera_scanner = None
        self._manager._camera_switch = None
        self.assertEqual(self._manager._camera_capture_alive(), False)

    def test_camera_capture_not_alive_when_cameras_scanner_none(self):
        self._manager._camera_scanner = None
        self.assertEqual(self._manager._camera_capture_alive(), False)

    def test_camera_capture_alive_when_cameras_switch_and_scanner_not_none(self):
        self.assertNotEqual(self._manager._camera_scanner, None)
        self.assertNotEqual(self._manager._camera_switch, None)
        self.assertEqual(self._manager._camera_capture_alive(), True)

    def test_cleanup_calls_kill_when_camera_capture_is_alive(self):
        self._manager._camera_scanner.kill.side_effect = self._kill_side_effect
        self.assertEqual(self._manager._camera_capture_alive(), True)
        self._manager._cleanup()
        self.assertEqual(self._manager._camera_capture_alive(), False)
        self.assertEqual(self._list_of_calls, [1]) # I had to do this as camera_sacnner is None after clean_up
        self.assertEqual(self._manager._camera_scanner, None)
        self.assertEqual(self._manager._camera_switch, None)

    def test_restart_live_capture_from_top_runs_the_camera_switch_method_once(self):
        self._manager._restart_live_capture_from_top()
        self._manager._camera_switch.restart_live_capture_from_top.assert_called_once()

    def test_restart_live_capture_from_side_runs_the_camera_switch_method_once(self):
        self._manager._restart_live_capture_from_side()
        self._manager._camera_switch.restart_live_capture_from_side.assert_called_once()

    def test_restart_live_capture_from_side_runs_reset_msg_timer(self):
        self._manager._record_msg_timer = MagicMock()
        self.assertNotEqual(self._manager._record_msg_timer, None)
        self._manager._restart_live_capture_from_side()
        self.assertEqual(self._manager._record_msg_timer, None)

    def test_reset_msg_timer(self):
        self._manager._record_msg_timer = MagicMock()
        self._manager._reset_msg_timer()
        self.assertEqual(self._manager._record_msg_timer, None)

    def test_start_msg_timer_starts_timer(self):
        self._manager._record_msg_timer = MagicMock()
        self._manager._start_msg_timer()
        self.assertNotEqual(self._manager._record_msg_timer, None)
        self.assertGreaterEqual(time.time(), self._manager._record_msg_timer)

    def test_msg_timer_is_running_returns_true_when_timer_not_none(self):
        self._manager._record_msg_timer = MagicMock()
        self.assertTrue(self._manager._msg_timer_is_running)

    def test__has_msg_timer_timeout(self):
        self._manager._record_msg_timer = time.time() - 3
        self.assertTrue(self._manager._has_msg_timer_timeout())


    #_read_message_queue
    # _read_view_queue
    # _read_result_queue
    # _read_side_scan
    # _read_top_scan




    def _kill_side_effect(self):
        self._list_of_calls.append(1)






