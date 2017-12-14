import unittest
from mock import MagicMock
from dls_barcode.data_store.record import Record
from dls_barcode.geometry.blank import BlankGeometry
from dls_barcode.plate import NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL

class TestRecord(unittest.TestCase):

    def test_from_string_creates_new_record_with_all_given_parameters(self):
        # Arrange
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"

        # Act
        r = Record.from_string(str)

        # Assert
        self.assertEqual(r.holder_barcode, 'DLSL-009')
        barcodes = r.barcodes
        self.assertEqual(len(barcodes), 3)
        self.assertTrue('DLSL-010' in barcodes)
        self.assertEquals(r.id, 'f59c92c1')
        self.assertEquals(r.timestamp, 1494238920.0)
        self.assertEquals(r.image_path, 'test.png')
        self.assertEquals(r.plate_type, 'None')
        self.assertTrue(isinstance(r.geometry, BlankGeometry))

    def test_from_string_creates_new_record_time_stamp_missing(self):
        # Arrange
        str = "f59c92c1; ;test.png;None;DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"

        # Act
        r = Record.from_string(str)

        # Assert
        self.assertEqual(r.holder_barcode, 'DLSL-009')
        barcodes = r.barcodes
        self.assertEqual(len(barcodes), 3)
        self.assertTrue('DLSL-010' in barcodes)
        self.assertEquals(r.id, 'f59c92c1')
        self.assertEquals(r.timestamp, 0.0) #could possibly generate a new timestamp instead
        self.assertEquals(r.image_path, 'test.png')
        self.assertEquals(r.plate_type, 'None')
        self.assertTrue(isinstance(r.geometry, BlankGeometry))

    def test_to_string_recreates_given_values_excluding_serial_number(self):
        # Arrange
        str = "f59c92c1;1494238920.0;test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        r = Record.from_string(str)

        # Act
        new_str = r.to_string()

        # Assert
        list_str = str.split(Record.ITEM_SEPARATOR)
        list_new_str = new_str.split(Record.ITEM_SEPARATOR)
        for i in range(len(list_str) - 1):
            self.assertTrue(list_str[i] == list_new_str[i])

    def test_csv_string_contains_time_in_human_readable_format(self):
        # Arrange
        timestamp = 1505913516.3836024

        # Full human readable timestamp is "2017-09-20 14:18:36" but Travis CI server runs on a different time zone so can't compare the hours
        human_readable_timestamp_day = "2017-09-20 "
        human_readable_timestamp_minutes = ":18:36"
        source_string = "f59c92c1;" + str(timestamp) + ";test.png;None;DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        record = Record.from_string(source_string)

        # Act
        csv_string = record.to_csv_string()

        # Assert
        self.assertIn(human_readable_timestamp_day, csv_string)
        self.assertIn(human_readable_timestamp_minutes, csv_string)
        self.assertNotIn(str(timestamp), csv_string)

    def test_record_can_be_constructed_from_plate_info(self):
        # Arrange
        plate_type = "plate type"
        holder_barcode = "ABCD"
        barcodes = ["barcode1", "barcode2"]
        image_path = "a_path"
        mock_geometry = MagicMock()
        mock_plate = self._create_mock_plate(plate_type, barcodes, mock_geometry)

        # Act
        r = Record.from_plate(holder_barcode, mock_plate, image_path)

        # Assert
        self.assertIsNotNone(r.timestamp)
        self.assertEquals(r.image_path, image_path)
        self.assertEquals(r.plate_type, plate_type)
        self.assertEquals(r.holder_barcode, holder_barcode)
        self.assertListEqual(r.barcodes, barcodes)
        self.assertEquals(r.geometry, mock_geometry)
        self.assertIsNotNone(r.id)

    def test_the_number_of_slots_are_counted_correctly_from_the_pin_barcodes(self):
        # Arrange
        barcodes = ["barcode1", "barcode2", EMPTY_SLOT_SYMBOL, "barcode3", NOT_FOUND_SLOT_SYMBOL, EMPTY_SLOT_SYMBOL]
        mock_plate = self._create_mock_plate("plate type", barcodes, MagicMock())

        # Act
        r = Record.from_plate(holder_barcode="ABCD", plate=mock_plate, image_path="a_path")

        # Assert
        self.assertEquals(r.num_slots, len(barcodes))
        self.assertEquals(r.num_empty_slots, 2)
        self.assertEquals(r.num_unread_slots, 1)
        self.assertEquals(r.num_valid_barcodes, 3)

    def _create_mock_plate(self, plate_type, barcodes, geometry):
        mock_plate = MagicMock()
        mock_plate.type = plate_type
        mock_plate.barcodes.return_value = barcodes
        mock_plate.geometry.return_value = geometry
        return mock_plate







