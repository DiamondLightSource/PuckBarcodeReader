import unittest

import time
from mock import MagicMock

from dls_barcode.data_store.backup import Backup

class TestBackup(unittest.TestCase):

    def setUp(self):
        self.comms_man = MagicMock()
        self.backup_time = MagicMock()
        weeks = 3
        WEEK_IN_SECONDS = 604800
        self.backup_time.value.return_value = weeks
        record_one = MagicMock(timestamp=time.time() - (weeks-1)*WEEK_IN_SECONDS)
        record_two = MagicMock(timestamp=time.time() - (weeks-2)*WEEK_IN_SECONDS)
        record_three = MagicMock(timestamp=time.time() - (weeks+1)*WEEK_IN_SECONDS)
        record_three.to_csv_string.return_value = 'csv_string_three'
        record_three.to_string.return_value = 'string_three'
        self.records = [record_one, record_two, record_three]

    def test_backup_records_to_csv_file(self):
        #Arrange
        self.comms_man.to_csv_file = MagicMock()
        backup = Backup(self.comms_man)

        # Act
        backup.backup_records([])

        #Assert
        self.comms_man.to_csv_file.assert_called_once()

