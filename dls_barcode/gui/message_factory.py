from dls_util.message import MessageType, Message


class MessageFactory:
    @staticmethod
    def latest_barcode_message():
        return Message(MessageType.WARNING, "Puck barcode already in latest record", lifetime=3)

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