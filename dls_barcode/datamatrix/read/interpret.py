import logging


class DatamatrixByteInterpreter:
    @staticmethod
    def interpret_bytes(data_bytes):
        """ Converts the raw set of bytes from the datamatrix into an ASCII .
        """
        DBI = DatamatrixByteInterpreter
        message = []

        i = 0
        eom_reached = False

        while not eom_reached and not i >= len(data_bytes):
            byte = data_bytes[i]

            if 1 <= byte < 129:  # ASCII.
                character = chr(byte - 1)
                message.append(character)
                i += 1

            elif byte == 129:  # EOM byte.
                eom_reached = True

            elif 130 <= byte < 230:  # Digit pairs 00-99.
                value = byte - 130
                digit_pair = str(value).zfill(2)
                message.append(digit_pair)
                i += 1

            elif byte == 230:  # Switch to C40 encoding scheme
                chars, num_bytes = DBI._interpret_text_mode_bytes(data_bytes[i:])
                message.extend(chars)
                i += num_bytes

            elif byte == 231:
                raise NotImplementedError("Datamatrix Base 256 decoding not implemented")

            elif 232 <= byte <= 237:  # Other parts of the Data Matrix spec., not supported.
                raise NotImplementedError("Datamatrix encoded symbol {} not implemented".format(byte))

            elif byte == 238:
                raise NotImplementedError("Datamatrix ANSI X12 decoding not implemented")

            elif byte == 239:
                chars, num_bytes = DBI._interpret_text_mode_bytes(data_bytes[i:])
                message.extend(chars)
                i += num_bytes

            elif byte == 240:
                #log = log = logging.getLogger(".".join([__name__]))
                #log.error(NotImplementedError("Datamatrix EDIFACT decoding not implemented"))
                raise NotImplementedError("Datamatrix EDIFACT decoding not implemented")

            elif byte == 241:
                #log = log = logging.getLogger(".".join([__name__]))
                #log.error(NotImplementedError("Datamatrix Extended Channel Interpretation code not implemented"))
                raise NotImplementedError("Datamatrix Extended Channel Interpretation code not implemented")

            elif 242 <= byte < 256:  # Unused parts of message space.
                #log = log = logging.getLogger(".".join([__name__]))
                error = ValueError("Code {} is not used in Datamatrix specification".format(byte))
                #.error(error)
                raise error
            elif byte == 0:
                error = ValueError("Code {} is not used in Datamatrix specification".format(byte))
                print(error)

        return ''.join(m for m in message)

    @staticmethod
    def _interpret_text_mode_bytes(data_bytes):
        """ For efficiency, Datamatrix encoding sometimes switches to the C40 encoding scheme
        which can encode 3 characters in 2 bytes, as long as the characters are digits or capital
        letters. This function decodes those bytes.
        """
        encoded_bytes = []
        mode = None
        for b in data_bytes:
            if b == 230:  # start of C40 encoding
                mode = "C40"
                continue

            elif b == 239:  # start of Text encoding
                mode = "Text"
                continue

            elif b == 254:  # end of c40 encoding
                break

            else:
                encoded_bytes.append(b)

        num_encoded_bytes = len(encoded_bytes)

        if num_encoded_bytes == 0:
            return ValueError("No data bytes encoded in Datamatrix Text Mode encoding")
        elif num_encoded_bytes % 2 != 0:
            raise ValueError("Odd number of Text mode encoded bytes")

        byte_pairs = [encoded_bytes[i:i + 2] for i in range(0, len(encoded_bytes), 2)]

        decoded_bytes = []
        DBI = DatamatrixByteInterpreter
        for pair in byte_pairs:
            decoded = DBI._decode_txt_mode_byte_pair(pair)
            decoded_bytes.extend(decoded)

        ascii_chars = [DBI._interpret_decoded_text_byte(byte, mode) for byte in decoded_bytes]

        num_bytes = num_encoded_bytes + 2
        return ascii_chars, num_bytes

    @staticmethod
    def _decode_txt_mode_byte_pair(byte_pair):
        """ Returns the original 3 bytes that are encoded in the byte pair. """
        i1 = byte_pair[0]
        i2 = byte_pair[1]

        val16 = (i1 * 256) + i2
        c1 = (val16 - 1) // 1600
        c2 = (val16 - (c1 * 1600)) // 40
        c3 = val16 - (c1 * 1600) - (c2 * 40) - 1

        return [c1, c2, c3]

    @staticmethod
    def _interpret_decoded_text_byte(byte, mode):
        """ Interpret the byte by lookup in the C40 or Text tables.

        C40 includes 4 encoding sets which each map the values 0-39 to a table of symbols. The first
        table is the default and includes the digits, capital letters, and the space character. The
        other tables contain the rest of the ascii characters including control characters. If the
        codes 0, 1, or 2 are used, it means that the next character should be read from table 1, 2,
        and 3 respectively.

        Text mode is exactly the same as C40 except that the upper and lower case characters are swapped
        """
        if mode not in ["C40", "Text"]:
            raise ValueError("Unrecognised Text encoding mode")

        if 0 <= byte <= 2:  # Used to switch to other encoding tables - not implemented here
            # Todo: implement the other tables
            raise NotImplementedError("{} Set 1, 2, and 3 encoding not implemented".format(mode))

        elif byte == 3:  # C40 3 is space
            return " "

        elif 4 <= byte <= 13:  # C40 number range, add 40 to get ascii value
            return chr(byte + 44)

        elif byte <= 39:  # C40 range A-Z, add 51 to get ascii value
            if mode == "C40":
                return chr(byte + 51)
            elif mode == "Text":
                return chr(byte + 83)

        else:
            raise ValueError("Value {} is not a valid C40 or Text symbol".format(byte))
