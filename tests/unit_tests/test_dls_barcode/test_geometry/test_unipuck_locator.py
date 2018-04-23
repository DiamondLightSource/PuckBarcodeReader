import unittest
from mock import MagicMock

import os

from dls_barcode.geometry.unipuck_locator import UnipuckLocator


class TestUnipuckLocator(unittest.TestCase):


    def test_read_feature_image_trows_exeption_when_no_image_found(self):
        path = os.path.join('.', 'resources', 'features', 'fit.png')
        self.assertRaises(IOError, UnipuckLocator(MagicMock())._read_feature_image, path)
