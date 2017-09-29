import unittest
from mock import MagicMock
import time

from dls_barcode.camera.plate_overlay import PlateOverlay


class TestPlateOverlay(unittest.TestCase):
    def setUp(self):
        self._plate = MagicMock()
        self._options = MagicMock()
        self._image = MagicMock()

    def test_overlay_has_default_lifetime(self):
        # Arrange
        expected_lifetime = 2

        # Act
        overlay = PlateOverlay(self._plate, self._options)

        # Assert
        time.sleep(expected_lifetime/2)
        self.assertFalse(overlay.has_expired())
        time.sleep(expected_lifetime / 2)
        self.assertTrue(overlay.has_expired())

    def test_lifetime_can_be_initialised(self):
        # Arrange
        lifetime = 0.2

        # Act
        overlay = PlateOverlay(self._plate, self._options, lifetime)

        # Assert
        time.sleep(lifetime)
        self.assertTrue(overlay.has_expired())

    def test_expired_overlay_is_not_drawn_on_image(self):
        # Arrange
        lifetime = 0.001
        overlay = PlateOverlay(self._plate, self._options, lifetime)

        # Act
        time.sleep(lifetime)
        overlay.draw_on_image(self._image)

        # Assert
        self._plate.draw_plate.assert_not_called()
        self._plate.draw_pins.assert_not_called()

    def test_not_expired_plate_is_drawn_on_image(self):
        # Arrange
        lifetime = 1000
        overlay = PlateOverlay(self._plate, self._options, lifetime)

        # Act
        overlay.draw_on_image(self._image)

        # Assert
        self._plate.draw_plate.assert_called_once()
        self._plate.draw_pins.assert_called_once()