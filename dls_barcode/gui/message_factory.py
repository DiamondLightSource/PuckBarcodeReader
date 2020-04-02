from dls_util.message import MessageType, Message


class MessageFactory:

    @staticmethod
    def from_scanner_message(scanner_msg):
        return Message(MessageType.WARNING, scanner_msg.content())

    @staticmethod
    def puck_recorded_message():
        return Message(MessageType.INFO, "Puck barcode recorded")

    @staticmethod
    def scan_timeout_message():
        return Message(MessageType.WARNING, "Scan timeout")

    @staticmethod
    def scan_completed_message():
        return Message(MessageType.INFO, "Scan completed")

    @staticmethod
    def puck_scan_completed_message():
        return Message(MessageType.INFO, "Scan completed!")

    @staticmethod
    def camera_not_found_message():
        return Message(MessageType.WARNING, "Cannot find specified camera!")
