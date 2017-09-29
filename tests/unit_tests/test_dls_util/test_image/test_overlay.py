import unittest
from mock import MagicMock
import time

from dls_util.image import TextOverlay


class TestTextOverlay(unittest.TestCase):
    def setUp(self):
        self._color = MagicMock()

    def test_overlay_has_default_lifetime(self):
        # Arrange
        expected_lifetime = 2

        # Act
        overlay = TextOverlay("blah", self._color)

        # Assert
        time.sleep(expected_lifetime/2)
        self.assertFalse(overlay.has_expired())
        time.sleep(expected_lifetime / 2)
        self.assertTrue(overlay.has_expired())

    def test_lifetime_can_be_initialised(self):
        # Arrange
        lifetime = 0.2

        # Act
        overlay = TextOverlay("blah", self._color, lifetime)

        # Assert
        time.sleep(lifetime)
        self.assertTrue(overlay.has_expired())

# Can't test the drawing method because overlay is passed an opencv image.
# It should be refactored to get an Image object instead of creating it itself
