from datetime import datetime
import time


class SessionManager:
    """Manages sessions. Gets a list of sessions from the"""

    def __init__(
        self, session_writer, store
    ):
        self.current_session_id = 0
        self.current_session_timestamp = ""
        self._session_writer = session_writer
        self._store = store

    def new_session(self):
        """Start a new session"""
        self.current_session_id = time.time()
        self.current_session_timestamp = datetime.fromtimestamp(
            self.current_session_id
        ).strftime("%H:%M:%S %d/%m/%Y")

    def end_session(self):
        """End a session"""
        self.current_session_id = 0
        self.current_session_timestamp = ""

    def save_session(self):
        "Save the records from a session"
        records = self._store.get_records_after_timestamp(self.current_session_id)
        self._session_writer.to_csv_file(records)
