from functools import partial

import numpy as np

from .exception import ReedSolomonError, DatamatrixDecoderError
from .interpret import DatamatrixByteInterpreter
from .reedsolo import ReedSolomonDecoder


class DatamatrixDecoder:
    """Class for decoding a datamatrix from an array of bits retrieving the data that is
    encoded by the barcode.
    """
    def __init__(self, num_data_bytes):
        self._num_data_bytes = num_data_bytes
        self._rs_decoder = ReedSolomonDecoder()

    def set_num_data_bytes(self, num_bytes):
        """ Set the number of bytes in the data matrix that encode data (the remaining  bytes
        are for error correction).
        """
        self._num_data_bytes = num_bytes

    def read_datamatrix(self, bit_array):
        """ Returns the string encoded by a data matrix bit array
        """
        encoded_bytes = self._extract_bytes(bit_array)
        decoded_bytes = self._correct_bytes(encoded_bytes)
        data = DatamatrixByteInterpreter.interpret_bytes(decoded_bytes)
        return data

    @staticmethod
    def _extract_bytes(bits):
        """Convert the array of bits into a set of raw bytes according to the datamatrix standard.
        The bytes require further processing before the actual message is retrieved.
        """
        n, m = bits.shape
        i, j = 4, 0
        read = np.zeros((n, m), dtype=np.int8)  # "Have we read this bit yet?"
        corner_read = 0  # "Which corner case was found?"
        data_bytes = []
        while True:
            if i == n and j == 0 and corner_read != 1:
                data_bytes.append(read_corner_case_1(bits, read, n, m))
                i -= 2;  j += 2;  corner_read = 1
            elif i == n - 2 and j == 0 and m & 0x03 != 0 and corner_read != 2:
                data_bytes.append(read_corner_case_2(bits, read, n, m))
                i -= 2;  j += 2;  corner_read = 2
            elif i == n + 4 and j == 2 and m & 0x07 != 0 and corner_read != 3:
                data_bytes.append(read_corner_case_3(bits, read, n, m))
                i -= 2;  j += 2;  corner_read = 3
            elif i == n - 2 and j == 0 and m & 0x07 != 4 and corner_read != 4:
                data_bytes.append(read_corner_case_4(bits, read, n, m))
                i -= 2;  j += 2;  corner_read = 4
            else:
                while True:
                    if i < n and j >= 0 and not read[i, j]:
                        data_bytes.append(read_utah(i, j, bits, read, n, m))
                    i -= 2;  j += 2
                    if not(i >= 0 and j < m):
                        break
                i += 1;  j += 3
                while True:
                    if i >= 0 and j < m and not read[i, j]:
                        data_bytes.append(read_utah(i, j, bits, read, n, m))
                    i += 2;  j -= 2
                    if not (i < n and j >= 0):
                        break
                i += 3;  j += 1
            if not(i < n or j < m):
                break
        return data_bytes

    def _correct_bytes(self, encoded_bytes):
        """Apply Reed-Solomon error correction to the set of raw bytes
        """
        try:
            decoded = self._rs_decoder.decode(encoded_bytes, self._num_data_bytes)
        except ReedSolomonError as ex:
            raise DatamatrixDecoderError("Unable to correct encoding errors: {}".format(str(ex)))

        return decoded


utah = lambda _, __: [  # (i, j), msb to lsb
    (-2, -2),
    (-2, -1),
    (-1, -2),
    (-1, -1),
    (-1,  0),
    ( 0, -2),
    ( 0, -1),
    ( 0,  0),
]

corner_case_1 = lambda n, m: [
    (n-1,   0),
    (n-1,   1),
    (n-1,   2),
    (  0, m-2),
    (  0, m-1),
    (  1, m-1),
    (  2, m-1),
    (  3, m-1),
]

corner_case_2 = lambda n, m: [
    (n-3,   0),
    (n-2,   0),
    (n-1,   0),
    (  0, m-4),
    (  0, m-3),
    (  0, m-2),
    (  0, m-1),
    (  1, m-1),
]

corner_case_3 = lambda n, m: [
    (n-1,   0),
    (n-1, m-1),
    (  0, m-3),
    (  0, m-2),
    (  0, m-1),
    (  1, m-3),
    (  1, m-2),
    (  1, m-1),
]

corner_case_4 = lambda n, m: [
    (n-3,   0),
    (n-2,   0),
    (n-1,   0),
    (  0, m-2),
    (  0, m-1),
    (  1, m-1),
    (  2, m-1),
    (  3, m-1),
]


def read_shape(shape, i, j, bits, read, n, m):
    return sum(1 << s
               for s, b
               # `reversed` flips endianness.
               in enumerate(reversed(list(
                   read_bit(i+r, j+c, bits, read, n, m)
                   for r, c in shape(n, m))))
               if b)

read_utah = partial(read_shape, utah)
read_corner_case_1 = partial(read_shape, corner_case_1, 0, 0)
read_corner_case_2 = partial(read_shape, corner_case_2, 0, 0)
read_corner_case_3 = partial(read_shape, corner_case_3, 0, 0)
read_corner_case_4 = partial(read_shape, corner_case_4, 0, 0)


def read_bit(i, j, bits, read, n, m):
    if i < 0:
        i += n
        j += 4 - ((n + 4) & 0x07)
    if j < 0:
        i += 4 - ((m + 4) & 0x07)
        j += m
    read[i, j] = 1
    return bits[i, j]