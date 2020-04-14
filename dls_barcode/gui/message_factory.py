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
        return Message(MessageType.WARNING, "camera can not be found.\nEnter the configuration to select the camera.", lifetime=0)

    @staticmethod
    def camera_params_not_integers_message():
        return Message(MessageType.WARNING, "Camera number, width, and height must be integers", lifetime=0)

    @staticmethod
    def camera_resolution_message(number, w, h, set_w, set_h):
        return Message(MessageType.WARNING, "Could not set the camera {} to the specified resolution: {}x{}.\nThe camera "
                                            "defaulted to {}x{}.".format(number, w, h, set_w, set_h), lifetime=0)

    @staticmethod
    def camera_empty_frame_message():
        return Message(MessageType.WARNING, "Camera returned an empty frame", lifetime=0)


