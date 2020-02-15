import unittest
from modules.devlugdispatch import MatterBridgeParser


class DevlugDispatcherTest(unittest.TestCase):

    def test_recognizes_matterbridge_message(self):
        """Test that a message was send by a matterbridge bot"""
        message = "[irc] <ancho> say something"
        parser = MatterBridgeParser()

        self.assertEqual(parser.validate(message), True)

    def test_parse_returns_None_for_none_matter_bridge_messages(self):
        """Test that a normal message gets parsed to None"""
        message = "a normal message"
        parser = MatterBridgeParser()

        self.assertEqual(parser.parse(message), None)

    def test_parse_returns_protocol_username_and_message(self):

        message = "[irc] <ancho> say something"
        parser = MatterBridgeParser()

        matter_msg = parser.parse(message)
        self.assertEqual(matter_msg.protocol, "irc")
        self.assertEqual(matter_msg.username, "ancho")
        self.assertEqual(matter_msg.message, "say something")
