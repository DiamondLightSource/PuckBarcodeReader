from datetime import datetime
import re
import time


class SessionManager:
    """Manages sessions. Gets a list of sessions from the"""

    def __init__(
        self, session_writer, store
    ):
        self.current_session_id = 0
        self.current_session_timestamp = ""
        self.visit_code = ""
        self._session_writer = session_writer
        self._store = store
        self._last_saved_file = ""

    def new_session(self, visit_code):
        """Start a new session"""
        self.current_session_id = time.time()
        self.visit_code = re.sub(r'[\\/*?:"<>|\ ]',"",visit_code)
        self.current_session_timestamp = datetime.fromtimestamp(
            self.current_session_id
        ).strftime("%H:%M:%S %d/%m/%Y")

    def edit_visit_code(self, new_visit_code):
        """Edit the visit code if session active"""
        success = bool(self.visit_code)
        if self.visit_code:
            self.visit_code = new_visit_code
        return success

    def end_session(self):
        """End a session"""
        self.current_session_id = 0
        self.current_session_timestamp = ""
        self.visit_code = ""

    def is_session_empty(self):
        records = self._store.get_records_after_timestamp(self.current_session_id)
        return not records

    def save_session(self):
        "Save the records from a session"
        records = self._store.get_records_after_timestamp(self.current_session_id)
        if records:
            file_time = datetime.fromtimestamp(self.current_session_id
                ).strftime("%H%M%S_%d%m%Y")
            session_fname = "{}_{}".format(self.visit_code, file_time)
            self._session_writer.set_file_name(session_fname)
            self._session_writer.to_csv_file(records)
            self.last_saved_file = self._session_writer.get_full_csv_path()
        records_saved = not not records
        return records_saved
