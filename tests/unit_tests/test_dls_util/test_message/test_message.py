import unittest
import time

from dls_util.message import Message, MessageType


class TestMessage(unittest.TestCase):
    def test_message_has_default_lifetime(self):
        # Arrange
        expected_lifetime = 2

        # Act
        msg = Message(MessageType.INFO, "hello")

        # Assert
        time.sleep(expected_lifetime/2)
        self.assertFalse(msg.has_expired())
        time.sleep(expected_lifetime / 2)
        self.assertTrue(msg.has_expired())

    def test_lifetime_can_be_initialised(self):
        # Arrange
        lifetime = 0.1

        # Act
        msg = Message(MessageType.INFO, "hello", lifetime)

        # Assert
        time.sleep(lifetime)
        self.assertTrue(msg.has_expired())

    def test_parameters_initalised_correctly(self):
        # Arrange
        type = MessageType.WARNING
        content = "hello there"

        # Act
        msg = Message(type, content)

        # Assert
        self.assertEqual(msg.type(), type)
        self.assertEqual(msg.content(), content)