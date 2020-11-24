import time
import unittest
from datetime import datetime
from mock import MagicMock
from mock import call, patch
from os import path
from dls_barcode.data_store import Store
from dls_barcode.data_store.session_manager import SessionManager
from dls_barcode.data_store.record import Record

VISIT_CODE = "tv12345 % ? <>"
VISIT_CODE_PROCESSED = "tv12345%"

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
        session.new_session(VISIT_CODE)

        # Assert
        self.assertEqual(session.current_session_id, 1494238922.0)

    def test_session_manager_illegal_characters_removed_from_visit_code(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)

        # Assert
        self.assertEqual(session.visit_code, VISIT_CODE_PROCESSED)

    @patch('time.time', MagicMock(return_value=1494238922.0))
    def test_session_manager_new_session_has_correct_timestamp(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)
        expected_timestamp = datetime.fromtimestamp(1494238922.0).strftime("%H:%M:%S %d/%m/%Y")

        # Assert
        self.assertEqual(session.current_session_timestamp, expected_timestamp)

    def test_session_manager_recognises_empty_session(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)
        self._store.get_records_after_timestamp.return_value = []
        is_session_empty = session.is_session_empty()

        # Assert
        self.assertTrue(is_session_empty)

    def test_session_manager_end_session_has_correct_timestamp(self):
        # Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)
        expected_id = 0

        #Act
        session.end_session()

        # Assert
        self.assertEqual(session.current_session_id, expected_id)

    def test_session_manager_saves_records(self):
        #Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)

        #Act
        session.save_session()

        #Assert
        self._session_writer.to_csv_file.assert_called()

    @patch('time.time', MagicMock(return_value=1494238922.0))
    def test_session_manager_sets_correct_fname(self):
        #Arrange
        session = self._create_session_manager()
        session.new_session(VISIT_CODE)
        expected_timestamp = datetime.fromtimestamp(1494238922.0).strftime("%H%M%S_%d%m%Y")
        expected_fname = path.join(VISIT_CODE_PROCESSED + "_" + expected_timestamp)

        #Act
        session.save_session()

        #Assert
        self._session_writer.set_file_name.assert_called_with(expected_fname)

    def _create_session_manager(self):
        return SessionManager(self._session_writer, self._store)
