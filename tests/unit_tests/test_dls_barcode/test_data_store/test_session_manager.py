import time
import unittest
from datetime import datetime
from mock import MagicMock
from mock import call, patch
from dls_barcode.data_store import Store
from dls_barcode.data_store.session_manager import SessionManager
from dls_barcode.data_store.record import Record

ID0 = "id0"
ID1 = "id1"
ID2 = "id2"
ID3 = "id3"

class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self._session_writer = MagicMock()
        self._session_writer._make_img_dir.return_value = "img_dir"
        self._expected_img_dir = "img_dir"
        self._store = MagicMock()
        self._store_writer = MagicMock()

    @patch('time.time', MagicMock(return_value=1494238922.0))
    def test_session_manager_new_session_has_correct_id(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session()

        # Assert
        self.assertEqual(session.current_session_id, 1494238922.0)

    @patch('time.time', MagicMock(return_value=1494238922.0))
    def test_session_manager_new_session_has_correct_timestamp(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session()
        expected_timestamp = datetime.fromtimestamp(1494238922.0).strftime("%H:%M:%S %d/%m/%Y")

        # Assert
        self.assertEqual(session.current_session_timestamp, expected_timestamp)

    def test_session_manager_end_session_has_correct_timestamp(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session()
        expected_id = 0

        #Act
        session.end_session()

        # Assert
        self.assertEqual(session.current_session_id, expected_id)

    def test_session_manager_saves_records(self):
        #Arrange
        session = self._create_session_manager()
        session.new_session()

        #Act
        session.save_session()

        #Assert
        self._session_writer.to_csv_file.assert_called()

    def _create_session_manager(self):
        return SessionManager(self._session_writer, self._store)
