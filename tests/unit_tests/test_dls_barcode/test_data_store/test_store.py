import unittest
from mock import MagicMock
from mock import call
import os
from dls_barcode.data_store import Store

ID0 = "id0"
ID1 = "id1"
ID2 = "id2"
ID3 = "id3"

class TestStore(unittest.TestCase):

    def setUp(self):
        self._file_manager = MagicMock()
        self._directory = "a_path"
        self._expected_img_dir = os.path.join(self._directory, "img_dir")
        self._expected_store_file = os.path.join(self._directory, "store.txt")
        self._expected_csv_file = os.path.join(self._directory, "store.csv")
        self._store_capacity = MagicMock()
        self._store_capacity.value.return_value = 50

        self._holder_img = MagicMock()
        self._pins_img = MagicMock()
        self._pins_img_copy = MagicMock()
        self._pins_img.copy.return_value = self._pins_img_copy

        self._plate = MagicMock()
        self._plate.type = "a_type"
        self._plate.barcodes.return_value = list()
        geometry = MagicMock()
        geometry.serialize.return_value = "123"
        self._plate.geometry.return_value = geometry

    def test_new_store_creates_image_directory_if_it_does_not_exist(self):
        # Arrange
        self._file_manager.is_dir.return_value = False
        self._file_manager.is_file.return_value = False

        # Act
        self._create_store()

        # Assert
        self._file_manager.make_dir.assert_called_once_with(self._expected_img_dir)

    def test_new_store_has_no_records_if_store_file_does_not_exist(self):
        # Arrange
        self._file_manager.is_file.return_value = False

        # Act
        store = self._create_store()

        # Assert
        self.assertFalse(store.records)
        self.assertEquals(store.size(), 0)

    def test_new_store_loads_records_from_existing_store_file(self):
        # Arrange
        record_strings = self._get_record_strings()
        self._file_manager.read_lines.return_value = record_strings

        # Act
        store = self._create_store()

        # Assert
        self.assertEquals(len(store.records), len(record_strings))
        self.assertEquals(store.size(), len(record_strings))
        self.assertEquals(store.records[0].id, ID0)
        self.assertEquals(store.records[1].id, ID1)
        self.assertEquals(store.records[2].id, ID2)
        self.assertEquals(store.records[3].id, ID3)

    def test_new_store_skips_invalid_lines_when_loading_records_from_file(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._invalid_record_strings()

        # Act
        store = self._create_store()

        # Assert
        self.assertEquals(len(store.records), 2)
        self.assertEquals(store.records[0].id, ID0)
        self.assertEquals(store.records[1].id, ID2)

    def test_max_number_of_stored_records_is_the_store_capacity(self):
        # Arrange
        record_strings = self._get_record_strings()
        self._file_manager.read_lines.return_value = record_strings
        expected_capacity = 3
        self._store_capacity.value.return_value = expected_capacity

        self.assertLess(expected_capacity, len(record_strings))

        # Act
        store = self._create_store()

        # Assert
        self.assertEquals(len(store.records), expected_capacity)
        self.assertEquals(store.records[0].id, ID0)
        self.assertEquals(store.records[1].id, ID1)
        self.assertEquals(store.records[2].id, ID2)

    def test_minimum_store_capacity_is_2(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        expected_capacity = 2
        self._store_capacity.value.return_value = 1

        # Act
        store = self._create_store()

        # Assert
        self.assertEquals(len(store.records), expected_capacity)

    def test_new_store_has_records_sorted_most_recent_first(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_unordered_record_strings()

        # Act
        store = self._create_store()

        # Assert
        for i in range(len(store.records) - 1):
            self.assertGreater(store.records[i].timestamp, store.records[i+1].timestamp)

    def test_a_record_can_be_retrieved_by_index(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        index = 1
        expected_id = ID1

        # Act
        r = store.get_record(index)

        # Assert
        self.assertEquals(r.id, expected_id)

    def test_get_record_returns_None_if_store_is_empty(self):
        # Arrange
        store = self._create_store()
        self.assertEquals(store.size(), 0)

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
        self._pins_img_copy.save_as.assert_called_once()
        ((image_filename_used,), kwargs) = self._pins_img_copy.save_as.call_args
        self.assertIn(self._expected_img_dir, image_filename_used)

    def test_given_an_empty_store_when_merging_a_record_then_the_record_is_added_to_the_store(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "ABCD"
        old_store_size = store.size()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), old_store_size + 1)
        r = store.get_record(0)
        self.assertEquals(r.holder_barcode, holder_barcode)

    def test_given_a_non_empty_store_when_merging_a_record_with_different_holder_than_the_latest_record_then_the_new_record_is_added(self):
        # Arrange
        holder1_barcode = "AAA"
        rec_string = "f59c92c1;1494238920.0;test.png;None;" + holder1_barcode + ",DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        self._file_manager.read_lines.return_value = [rec_string]
        store = self._create_store()
        old_store_size = store.size()

        holder2_barcode = "BBB"

        # Act
        store.merge_record(holder2_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), old_store_size + 1)
        self.assertEquals(store.records[0].holder_barcode, holder2_barcode)
        self.assertEquals(store.records[1].holder_barcode, holder1_barcode)

    def test_given_a_non_empty_store_when_merging_a_record_with_same_holder_to_the_latest_record_then_latest_record_is_replaced(self):
        # Arrange
        holder_barcode = "ABCDE123"
        old_pin_barcode = "DLSL-009"
        new_pin_barcodes = ["DLSL-010"]
        rec_string = "f59c92c1;1494238920.0;test.png;None;" + holder_barcode + "," + old_pin_barcode + ";1569:1106:70-2307:1073:68-1944:1071:68"
        self._file_manager.read_lines.return_value = [rec_string]
        store = self._create_store()
        old_store_size = store.size()

        self._plate.barcodes.return_value = new_pin_barcodes

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), old_store_size)
        r = store.records[0]
        self.assertEquals(r.holder_barcode, holder_barcode)
        self.assertListEqual(r.barcodes, new_pin_barcodes)

    def test_duplicate_holder_barcodes_are_allowed_if_the_duplicate_is_not_the_latest_record(self):
        # Arrange
        holder_barcode = "ABD1234"
        rec_strings = self._get_record_strings()
        duplicate_rec_string = "f59c92c1;1494238900.0;test.png;None;" + holder_barcode + ",DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68"
        rec_strings.append(duplicate_rec_string)
        self._file_manager.read_lines.return_value = rec_strings
        store = self._create_store()
        old_store_size = store.size()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), old_store_size + 1)
        duplicates = [r for r in store.records if r.holder_barcode == holder_barcode]
        self.assertEquals(len(duplicates), 2)

    def test_given_a_store_when_merging_a_record_then_store_is_saved_to_backing_file(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "ABAB"
        self._file_manager.write_lines.assert_not_called()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self._file_manager.write_lines.assert_called()
        ((filename_used, record_lines_used), kwargs) = self._file_manager.write_lines.call_args_list[0]
        self.assertEquals(filename_used, self._expected_store_file)
        self.assertIn(holder_barcode, record_lines_used[0])

    def test_given_a_store_when_merging_a_record_then_store_is_saved_to_csv_file(self):
        # Arrange
        store = self._create_store()
        holder_barcode = "HELLO"
        self._file_manager.write_lines.assert_not_called()

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self._file_manager.write_lines.assert_called()
        ((filename_used, record_lines_used), kwargs) = self._file_manager.write_lines.call_args_list[1]
        self.assertEquals(filename_used, self._expected_csv_file)
        self.assertIn(holder_barcode, record_lines_used[0])

    def test_given_a_non_empty_store_of_size_equal_to_capacity_when_a_new_record_is_merged_then_oldest_record_is_deleted(self):
        # Arrange
        capacity = 4
        self._store_capacity.value.return_value = capacity
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        old_store_size = store.size()
        self.assertEquals(old_store_size, capacity)
        holder_barcode = "asd"
        oldest_record = store.records[-1]

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), old_store_size)
        latest_rec = store.get_record(0)
        self.assertEquals(latest_rec.holder_barcode, holder_barcode)
        self.assertNotIn(oldest_record, store.records)

    def test_multiple_records_can_be_deleted(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        old_store_size = store.size()
        records_to_delete =[r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self.assertEquals(store.size(), old_store_size - len(records_to_delete))
        for r in records_to_delete:
            self.assertNotIn(r, store.records)

    def test_when_records_are_deleted_then_their_image_file_is_deleted_too(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._file_manager.remove.assert_not_called()

        expected_calls = []
        for r in records_to_delete:
            expected_calls.append(call(r.image_path))

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._file_manager.remove.assert_has_calls(expected_calls)

    def test_when_records_are_deleted_then_store_file_is_updated(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._file_manager.write_lines.assert_not_called()

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._file_manager.write_lines.assert_called()
        ((filename_used, record_lines_used), kwargs) = self._file_manager.write_lines.call_args_list[0]
        self.assertEquals(filename_used, self._expected_store_file)
        self.assertEquals(len(record_lines_used), store.size())
        for r, l in zip(store.records, record_lines_used):
            self.assertIn(r.to_string(), l)

    def test_when_records_are_deleted_then_csv_file_is_updated(self):
        # Arrange
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        records_to_delete = [r for r in store.records if r.id == ID1 or r.id == ID3]
        self.assertTrue(records_to_delete)
        self._file_manager.write_lines.assert_not_called()

        # Act
        store.delete_records(records_to_delete)

        # Assert
        self._file_manager.write_lines.assert_called()
        ((filename_used, record_lines_used), kwargs) = self._file_manager.write_lines.call_args_list[1]
        self.assertEquals(filename_used, self._expected_csv_file)
        self.assertEquals(len(record_lines_used), store.size())
        for r, l in zip(store.records, record_lines_used):
            self.assertIn(r.to_csv_string(), l)

    def test_given_a_non_empty_store_when_capacity_is_reduced_then_records_are_truncated_at_next_merge(self):
        # Arrange
        old_capacity = 4
        self._store_capacity.value.return_value = old_capacity
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        self.assertEquals(store.size(), old_capacity)

        new_capacity = 2
        self._store_capacity.value.return_value = new_capacity
        holder_barcode = "asd"
        expected_truncated_records = store.records[1:3]
        self.assertTrue(expected_truncated_records)

        # Act
        store.merge_record(holder_barcode, self._plate, self._holder_img, self._pins_img)

        # Assert
        self.assertEquals(store.size(), new_capacity)
        latest_rec = store.get_record(0)
        self.assertEquals(latest_rec.holder_barcode, holder_barcode)
        for r in expected_truncated_records:
            self.assertNotIn(r, store.records)

    def test_given_a_non_empty_store_when_capacity_is_reduced_then_records_are_truncated_at_next_delete(self):
        # Arrange
        old_capacity = 4
        self._store_capacity.value.return_value = old_capacity
        self._file_manager.read_lines.return_value = self._get_record_strings()
        store = self._create_store()
        self.assertEquals(store.size(), old_capacity)

        new_capacity = 2
        self._store_capacity.value.return_value = new_capacity
        record_to_delete = store.records[1]
        expected_truncated_record = store.records[3]

        # Act
        store.delete_records([record_to_delete])

        # Assert
        self.assertEquals(store.size(), new_capacity)
        self.assertNotIn(record_to_delete, store.records)
        self.assertNotIn(expected_truncated_record, store.records)

    def _create_store(self):
        return Store(self._directory, self._store_capacity, self._file_manager)

    def _get_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238923.0;test" + ID0 + ".png;None;DLSL-001,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";1494238922.0;test" + ID1 + ".png;None;DLSL-002,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID2 + ";1494238921.0;test" + ID2 + ".png;None;DLSL-003,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID3 + ";1494238920.0;test" + ID3 + ".png;None;DLSL-004,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

    def _get_unordered_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238905.0;test" + ID0 + ".png;None;DLSL-001,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";1494238921.0;test" + ID1 + ".png;None;DLSL-002,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID2 + ";1494238901.0;test" + ID2 + ".png;None;DLSL-003,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID3 + ";1494238930.0;test" + ID3 + ".png;None;DLSL-004,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

    def _invalid_record_strings(self):
        str_rep = list()
        str_rep.append(ID0 + ";1494238925.0;test.png;None;DLSL-009,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        str_rep.append(ID1 + ";Invalid record string")
        str_rep.append(ID2 + ";1494238921.0;test.png;None;DLSL-008,DLSL-010,DLSL-011,DLSL-012;1569:1106:70-2307:1073:68-1944:1071:68")
        return str_rep

