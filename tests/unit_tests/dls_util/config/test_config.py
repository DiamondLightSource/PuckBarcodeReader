import unittest

from dls_barcode.config import BarcodeConfig
from dls_util import Config


class TestConfig(unittest.TestCase):

    def test_init_creates_empty_item_table(self):
        cof = Config('config.ini')
        items = cof._items
        self.assertEquals(len(items), 0)



