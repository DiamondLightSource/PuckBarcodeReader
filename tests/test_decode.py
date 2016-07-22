import unittest
from dls_barcode.datamatrix.decode import Decoder


cases = [
    ([85, 102, 116, 117, 129], "Test"),
    ([85, 102, 116, 117, 129, 101, 102, 103], "Test"),
    ([69, 71, 145, 49, 70, 134, 173, 129], "DF150E0443"),
    ([x+1 for x in range(32, 127)], str(bytearray([x for x in range(32, 127)]), 'utf-8'))
]


class TestDecode(unittest.TestCase):
    def test_datamatrix_decode(self):
        decoder = Decoder()

        for bytes, message in cases:
            dec = decoder._interpret_bytes(bytes)
            assert dec == message

if __name__ == '__main__':
    unittest.main()