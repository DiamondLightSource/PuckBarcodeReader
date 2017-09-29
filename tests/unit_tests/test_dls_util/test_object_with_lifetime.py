import unittest
import time
from dls_util.object_with_lifetime import ObjectWithLifetime


class TestObjectWithLifetime(unittest.TestCase):
    def test_object_with_life_less_than_lifetime_has_not_expired(self):
        # Arrange
        lifetime = 0.5

        # Act
        obj = ObjectWithLifetime(lifetime)

        # Assert
        self.assertFalse(obj.has_expired())

    def test_object_with_life_greater_than_lifetime_has_expired(self):
        # Arrange
        lifetime = 0.5

        # Act
        obj = ObjectWithLifetime(lifetime)
        time.sleep(lifetime)

        # Assert
        self.assertTrue(obj.has_expired())
