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

    def test_truncate_removes_all_old_records(self):
        # Arrange
        self.comms_man.load_records_from_file.return_value = self.records

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        orig_size = len(backup._records)
        backup._truncate_record_list()

        # Assert
        new_size = len(backup._records)
        self.assertNotEqual(orig_size, new_size)
        self.assertEqual(new_size, 2)

    def test_backup_records_adds_new_records_to_existing_list(self):
        # Arrange
        self.comms_man.load_records_from_file.return_value = self.records

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        backup.backup_records(self.records)

        # Assert
        self.assertEqual(len(backup._records), 4) #old truncated

    def test_backup_records_removes_old_records_from_the_passed_when_its_called(self):
        # Arrange
        self.comms_man.load_records_from_file.return_value = []

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        backup.backup_records(self.records)

        # Assert
        self.assertEqual(len(backup._records), 2)

    def test_backup_records_to_csv_file(self):
        #Arrange
        self.comms_man.to_csv_file = MagicMock()
        backup = Backup(self.comms_man, self.backup_time)

        # Act
        backup.backup_records([])

        #Assert
        self.comms_man.to_csv_file.assert_called_once()

    def test_is_old_returns_true_for_records_older_than_assumed_number_of_weeks(self):
        # Arrange
        record = self.records[2]

        # Act
        backup = Backup(self.comms_man, self.backup_time)

        # Assert
        self.assertTrue(backup._is_old(record))

    def test_is_old_returns_false_for_records_younger_than_assumed_number_of_weeks(self):
        # Arrange
        record = self.records[0]

        # Act
        backup = Backup(self.comms_man, self.backup_time)

        # Assert
        self.assertFalse(backup._is_old(record))
