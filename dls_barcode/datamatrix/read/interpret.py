class DatamatrixByteInterpreter:
    @staticmethod
    def interpret_bytes(data_bytes):
        """ Converts the raw set of bytes from the datamatrix into an ASCII .
        """
        message = []

        i = 0
        eom_reached = False

        while not eom_reached:
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
                chars, num_bytes = DatamatrixByteInterpreter._interpret_c40_bytes(data_bytes[i:])
                message.extend(chars)
                i += num_bytes

            elif byte == 231:
                raise NotImplementedError("Datamatrix Base 256 decoding not implemented")

            elif 232 <= byte <= 237:  # Other parts of the Data Matrix spec., not supported.
                raise NotImplementedError("Datamatrix encoded symbol {} not implemented".format(byte))

            elif byte == 238:
                raise NotImplementedError("Datamatrix ANSI X12 decoding not implemented")

            elif byte == 239:
                raise NotImplementedError("Datamatrix Text decoding not implemented")

            elif byte == 240:
                raise NotImplementedError("Datamatrix EDIFACT decoding not implemented")

            elif byte == 241:
                raise NotImplementedError("Datamatrix Extended Channel Interpretation code not implemented")

            elif 242 <= byte < 256 or byte == 0:  # Unused parts of message space.
                raise ValueError("Code {} is not used in Datamatrix specification".format(byte))

        return ''.join(m for m in message)

    @staticmethod
    def _interpret_c40_bytes(data_bytes):
        """ For efficiency, Datamatrix encoding sometimes switches to the C40 encoding scheme
        which can encode 3 characters in 2 bytes, as long as the characters are digits or capital
        letters. This function decodes those bytes.
        """
        c40_encoded_bytes = []
        for b in data_bytes:
            if b == 230:  # start of C40 encoding
                continue
            elif b == 254:  # end of c40 encoding
                break
            else:
                c40_encoded_bytes.append(b)

        num_encoded_bytes = len(c40_encoded_bytes)

        if num_encoded_bytes == 0:
            return [], 2

        elif num_encoded_bytes % 2 != 0:
            raise ValueError("Odd number of C40 encoded bytes")

        byte_pairs = [c40_encoded_bytes[i:i + 2] for i in range(0, len(c40_encoded_bytes), 2)]

        ascii_chars = []
        for pair in byte_pairs:
            i1 = pair[0]
            i2 = pair[1]

            val16 = (i1 * 256) + i2
            c1 = (val16 - 1) // 1600
            c2 = (val16 - (c1 * 1600)) // 40
            c3 = val16 - (c1 * 1600) - (c2 * 40) - 1

            chars = [DatamatrixByteInterpreter._interpret_decoded_c40_byte(byte) for byte in [c1, c2, c3]]
            ascii_chars.extend(chars)

        num_bytes = num_encoded_bytes + 2
        return ascii_chars, num_bytes

    @staticmethod
    def _interpret_decoded_c40_byte(byte):
        """ Interpret the byte by lookup in the C40 table.

        C40 includes 4 encoding sets which each map the values 0-39 to a table of symbols. The first
        table is the default and includes the digits, capital letters, and the space character. The
        other tables contain the rest of the ascii characters including control characters. If the
        codes 0, 1, or 2 are used, it means that the next character should be read from table 1, 2,
        and 3 respectively.
        """
        if 0 <= byte <= 2:  # Used to switch to other encoding tables - not implemented here
            # Todo: implement the other tables
            raise NotImplementedError("Alternative C40 encoding sets not implemented")

        elif byte == 3:  # C40 3 is space
            return " "

        elif 4 <= byte <= 13:  # C40 number range, add 40 to get ascii value
            return chr(byte + 44)

        elif byte <= 39:  # C40 range A-Z, add 51 to get ascii value
            return chr(byte + 51)

        else:
            raise ValueError("Value {} is not a Recognised C40 symbol".format(byte))

