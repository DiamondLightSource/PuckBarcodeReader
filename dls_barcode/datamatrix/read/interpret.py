class DatamatrixByteInterpreter:
    @staticmethod
    def interpret_bytes(data_bytes):
        """ Converts the raw set of bytes from the datamatrix into an ASCII .
        """
        message = []
        for byte in data_bytes:
            if 1 <= byte < 129:  # ASCII.
                character = chr(byte - 1)
                message.append(character)

            elif byte == 129:  # EOM byte.
                break

            elif 130 <= byte < 230:  # Digit pairs 00-99.
                value = byte - 130
                digit_pair = str(value).zfill(2)
                message.append(digit_pair)

            elif 230 <= byte < 242:
                # Other parts of the Data Matrix spec., not supported.
                pass

            elif 242 <= byte < 256 or byte == 0:  # Unused parts of message space.
                pass

        return ''.join(m for m in message)
