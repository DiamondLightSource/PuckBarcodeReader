import unittest
from mock import MagicMock
from mock import call
from dls_barcode.data_store import Store
from dls_barcode.data_store.record import Record

ID0 = "id0"
ID1 = "id1"
ID2 = "id2"
ID3 = "id3"


class TestStore(unittest.TestCase):

    def setUp(self):
        self._backup = MagicMock()
        self._store_writer = MagicMock()
        self._store_writer._make_img_dir.return_value = "img_dir"
        self._expected_img_dir = "img_dir"

        self._holder_img = MagicMock()
        self._pins_img = MagicMock()

        self._plate = MagicMock()
        self._plate.type = "a_type"
        self._plate.barcodes.return_value = list()
        geometry = MagicMock()
        geometry.serialize.return_value = "123"
        self._plate.geometry.return_value = geometry

    def test_a_record_can_be_retrieved_by_index(self):
        # Arrange
        store = self._create_store()
        index = 1
        expected_id = ID1

        # Act
        r = store.get_record(index)

        # Assert
        self.assertEqual(r.id, expected_id)

    def test_get_record_returns_None_if_store_is_empty(self):
        # Arrange
        store = self._create_empty_store()
        self.assertEqual(store.size(), 0)

        # Act
        r = store.get_record(0)

        # Assert
        self.assertIsNone(r)

    def test_given_a_store_when_merging_a_record_then_an_image_is_saved_to_file(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "ABC"

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self._store_writer.to_image.assert_called_once()
        ((image, file_name,), kwargs) = self._store_writer.to_image.call_args
        self.assertIsNotNone(file_name)

    def test_given_an_empty_store_when_merging_a_record_then_the_record_is_added_to_the_store(self):
        # Arrange
        store = self._create_empty_store()
        holder_barcode = "ABCD"
        old_store_size = store.size()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEqual(store.size(), old_store_size + 1)
        r = store.get_record(0)
        self.assertEqual(r.holder_barcode, holder_barcode)

    def test_given_a_non_empty_store_when_merging_a_record_with_different_holder_than_the_latest_record_then_the_new_record_is_added(self):
        # Arrange
        holder1_barcode = "AAA"
        rec_string = "f59c92c1;1494238920.0;test.png;None;" + holder1_barcode + ",DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        store = self._create_store_with_records([Record.from_string(rec_string)])
        old_store_size = store.size()

        holder2_barcode = "BBB"

        # Act
        store.merge_record(holder2_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEqual(store.size(), old_store_size + 1)
        self.assertEqual(store.records[0].holder_barcode, holder2_barcode)
        self.assertEqual(store.records[1].holder_barcode, holder1_barcode)

    def test_given_a_non_empty_store_when_merging_a_record_with_same_holder_to_the_latest_record_then_latest_record_is_replaced(self):
        # Arrange
        holder_barcode = "ABCDE123"
        old_pin_barcode = "DLSL-009"
        new_pin_barcodes = ["DLSL-010"]
        rec_string = "f59c92c1;1494238920.0;test.png;None;" + holder_barcode + "," + old_pin_barcode + ";1569:1106:70-2307:1073:68-1944:1071:68"
        store = self._create_store_with_records([Record.from_string(rec_string)])
        old_store_size = store.size()

        self._plate.barcodes.return_value = new_pin_barcodes

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEqual(store.size(), old_store_size)
        r = store.records[0]
        self.assertEqual(r.holder_barcode, holder_barcode)
        self.assertListEqual(r.barcodes, new_pin_barcodes)

    def test_duplicate_holder_barcodes_are_allowed_if_the_duplicate_is_not_the_latest_record(self):
        # Arrange
        holder_barcode = "ABD1234"
        recs = self._get_records()
        duplicate_rec_string = "f59c92c1;1494238900.0;test.png;None;" + holder_barcode + ",DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        recs.append(Record.from_string(duplicate_rec_string))
        store = self._create_store_with_records(recs)
        old_store_size = store.size()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEqual(store.size(), old_store_size + 1)
        duplicates = [r for r in store.records if r.holder_barcode == holder_barcode]
        self.assertEqual(len(duplicates), 2)

    def test_given_a_store_when_merging_a_record_then_store_is_saved_to_backing_file(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "ABAB"
        self._store_writer.to_file.assert_not_called()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self._store_writer.to_file.assert_called()

    def test_given_a_store_when_merging_a_record_then_store_is_saved_to_csv_file(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "HELLO"
        self._store_writer.to_csv_file.assert_not_called()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self._store_writer.to_csv_file.assert_called()

    def test_multiple_records_can_be_deleted(self):
        # Arrange
        self._store_writer.load_records_from_file.return_value = self._get_records()
        store = self._create_store()
        old_store_size = store.size()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self.assertEqual(store.size(), old_store_size - len(records_to_delete))
        for r in records_to_delete:
            self.assertNotIn(r, store.records)

    def test_when_records_are_deleted_then_their_image_file_is_deleted_too(self):
        # Arrange
        self._store_writer.load_records_from_file.return_value = self._get_records()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._store_writer.remove_img_file.assert_not_called()

        expected_calls = []
        for r in records_to_delete:
            expected_calls.append(call(r))

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._store_writer.remove_img_file.assert_has_calls(expected_calls)

    def test_when_records_are_deleted_then_store_file_is_updated(self):
        # Arrange
        self._store_writer.load_records_from_file.return_value = self._get_records()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._store_writer.to_file.assert_not_called()

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._store_writer.to_file.assert_called()
        ((record_lines_used), kwargs) = self._store_writer.to_file.call_args_list[0]
        self.assertEqual(len(record_lines_used[0]), store.size())
        for r, l in zip(store.records, record_lines_used):
            self.assertIn(r, l)

    def test_when_records_are_deleted_then_csv_file_is_updated(self):
        # Arrange
        self._store_writer.load_records_from_file.return_value = self._get_records()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._store_writer.to_csv_file.assert_not_called()

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._store_writer.to_csv_file.assert_called()

        ((record_lines_used), kwargs) = self._store_writer.to_csv_file.call_args_list[0]
        self.assertEqual(len(record_lines_used[0]), store.size())
        for r, l in zip(store.records, record_lines_used):
            self.assertIn(r, l)

    def _create_store(self):
        return Store(self._store_writer, self._get_records())

    def _create_store_with_records(self, records):
        return Store(self._store_writer, records)

    def _create_empty_store(self):
        return Store(self._store_writer, [])

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

