import unittest

from mock import Mock, patch

from dls_barcode.datamatrix.datamatrix import DataMatrix

class TestDatamatrix(unittest.TestCase):

    def test_contains_allowed_characers(self):
        datamatrix = DataMatrix(Mock)
        test_string_good = "AbcD123_-"
        self.assertTrue(datamatrix._contains_allowed_chars_only(test_string_good))

        test_string_bad = "AbcD123_-$<"
        self.assertFalse(datamatrix._contains_allowed_chars_only(test_string_bad))


            

