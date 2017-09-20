import unittest
from dls_barcode.data_store.record import Record
from dls_barcode.geometry.blank import BlankGeometry

class TestRecord(unittest.TestCase):

    def test_from_string_creates_new_record_with_all_given_parameters(self):
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        barcodes = r.barcodes
        self.assertEqual(len(barcodes), 3)
        self.assertTrue('DLSL-010' in barcodes)
        self.assertEquals(r.id, 'f59c92c1')
        self.assertEquals(r.timestamp, 1494238920.0)
        self.assertEquals(r.image_path, 'test.png')
        self.assertEquals(r.plate_type, 'None')
        self.assertTrue(isinstance(r.geometry, BlankGeometry))


    def test_from_string_creates_new_record_time_stamp_missing(self):
        str = "f59c92c1; ;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        barcodes = r.barcodes
        self.assertEqual(len(barcodes), 3)
        self.assertTrue('DLSL-010' in barcodes)
        self.assertEquals(r.id, 'f59c92c1')
        self.assertEquals(r.timestamp, 0.0) #could possibly generate a new timestamp instead
        self.assertEquals(r.image_path, 'test.png')
        self.assertEquals(r.plate_type, 'None')
        self.assertTrue(isinstance(r.geometry, BlankGeometry))

    def test_to_string_recreates_given_values_excluding_serial_number(self):
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)
        new_str = r.to_string()
        list_str = str.split(Record.ITEM_SEPARATOR)
        list_new_str = new_str.split(Record.ITEM_SEPARATOR)
        i = 0
        while (i < len(list_str)-1):
            self.assertTrue(list_str[i] == list_new_str[i])
            i = i+1

    def test_any_barcode_matches_returns_true_if_only_one_barcode_matches(self):
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        self.assertTrue(r.any_barcode_matches(['DLSL-010','DLSL-011111']))

    def test_any_barcode_matches_returns_false_if_no_barcode_match(self):
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        self.assertFalse(r.any_barcode_matches(['DLSL', 'DLSL3']))

    def test_any_barcode_matches_returns_false_if_no_barcodes_passed(self):
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        self.assertFalse(r.any_barcode_matches([]))

    def test_csv_string_contains_time_in_human_readable_format(self):
        # Arrange
        timestamp = 1505913516.3836024
        human_readable_timestamp = "2017-09-20 14:18:36"
        source_string = "f59c92c1;" + str(timestamp) + ";test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        record = Record.from_string(source_string)

        # Act
        csv_string = record.to_csv_string()

        # Assert
        self.assertIn(human_readable_timestamp, csv_string)
        self.assertNotIn(str(timestamp), csv_string)







