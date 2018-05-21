from dls_util.message import MessageType, Message


class MessageFactory:

    @staticmethod
    def puck_recorded_message():
        return Message(MessageType.INFO, "Puck barcode recorded")

    @staticmethod
    def scan_timeout_message():
        return Message(MessageType.WARNING, "Scan timeout")

    @staticmethod
    def scan_completed_message():
        return Message(MessageType.INFO, "Scan completed")