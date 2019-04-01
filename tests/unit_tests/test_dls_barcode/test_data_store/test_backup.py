import unittest

import time
from mock import MagicMock

from dls_barcode.data_store.backup import Backup
from dls_barcode.data_store.record import Record

ID0 = "id0"
ID1 = "id1"
ID2 = "id2"
ID3 = "id3"

class TestBackup(unittest.TestCase):

    def setUp(self):
        self.comms_man = MagicMock()
        self.backup_time = MagicMock()
        self.backup_time.value.return_value = 3

    def test_truncate_removes_all_old_records(self):
        # Arrange
        records = self._get_records()
        self.comms_man.load_records_from_file.return_value = records

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        orig_size = len(backup._records)
        backup._truncate_record_list()

        # Assert
        new_size = len(backup._records)
        self.assertNotEqual(orig_size, new_size)
        self.assertEqual(new_size, 0)

    def test_backup_records_adds_new_records_to_existing_list(self):
        # Arrange
        records = self._get_records()
        self.comms_man.load_records_from_file.return_value = records

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        org_size = len(backup._records)
        backup._truncate_record_list = MagicMock() #mute truncate for the test
        backup.backup_records(records)

        # Assert
        self.assertEqual(len(backup._records), 2*org_size)

    def test_backup_records_removes_old_records_when_its_called(self):
        # Arrange
        records = self._get_records()
        self.comms_man.load_records_from_file.return_value = records

        # Act
        backup = Backup(self.comms_man, self.backup_time)
        backup.backup_records(records)

        # Assert
        self.assertEqual(len(backup._records), 0)

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
        weeks = self.backup_time.value.return_value
        timestamp = str(time.time() - 604800 * (weeks + 1))
        rec_string = "f59c92c1;" + timestamp + ";test.png;None;ABCDE123,ABCDE123;1569:1106:70-2307:1073:68-1944:1071:68"
        record = Record.from_string(rec_string)

        # Act
        backup = Backup(self.comms_man, self.backup_time)

        # Assert
        self.assertTrue(backup._is_old(record))

    def test_is_old_returns_false_for_records_younger_than_assumed_number_of_weeks(self):
        # Arrange
        weeks = self.backup_time.value.return_value
        timestamp = str(time.time() - 604800 * (weeks - 1))
        rec_string = "f59c92c1;"+timestamp+";test.png;None;ABCDE123,ABCDE123;1569:1106:70-2307:1073:68-1944:1071:68"
        record = Record.from_string(rec_string)

        # Act
        backup = Backup(self.comms_man, self.backup_time)

        # Assert
        self.assertFalse(backup._is_old(record))

    def _get_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238923.0;test" + ID0 + ".png;None;DLSL-001,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";1494238922.0;test" + ID1 + ".png;None;DLSL-002,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID2 + ";1494238921.0;test" + ID2 + ".png;None;DLSL-003,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID3 + ";1494238920.0;test" + ID3 + ".png;None;DLSL-004,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

    def _get_records(self):
        strings = self._get_record_strings()
        rep = list()
        for str in strings:
            rep.append(Record.from_string(str))
        return rep