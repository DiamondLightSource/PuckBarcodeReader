import unittest

from dls_barcode.datamatrix.reedsolo import ReedSolomonDecoder, ReedSolomonError


"""
The example datamatrix message "DF150E0443" appropriately encoded for datamatrix is:
    [69, 71, 145, 49, 70, 134, 173, 129]
after Reed-Solomon encoding this is:
    [69, 71, 145, 49, 70, 134, 173, 129, 195, 218, 3, 144, 228, 239, 62, 153, 67, 12]

The message has 8 bytes and 10 ECC characters, this means that it can fully recover the
original message as long as no more than 5 (=10/2) bytes are damaged.

A ReedSolomonError is raised if the decoding fails
"""
num_ecc_bytes = 10
msg_bytes = [69, 71, 145, 49, 70, 134, 173, 129]
msg_bytes_encoded = [69, 71, 145, 49, 70, 134, 173, 129, 195, 218, 3, 144, 228, 239, 62, 153, 67, 12]
msg_bytes_correctable = [
    [69, 71, 0, 49, 70, 134, 173, 129, 195, 218, 3, 144, 228, 239, 62, 153, 67, 12],  # 1 error
    [0, 71, 145, 49, 70, 134, 173, 129, 195, 0, 3, 144, 228, 239, 62, 153, 67, 12],   # 2 errors
    [69, 0, 145, 49, 70, 0, 173, 129, 195, 218, 3, 144, 228, 239, 62, 0, 67, 12],     # 3 errors
    [69, 71, 145, 49, 0, 134, 173, 129, 195, 0, 0, 0, 228, 239, 62, 153, 67, 12],     # 4 errors
    [0, 0, 0, 0, 0, 134, 173, 129, 195, 218, 3, 144, 228, 239, 62, 153, 67, 12],      # 5 errors
    [69, 71, 145, 49, 70, 134, 173, 129, 195, 218, 3, 144, 228, 0, 0, 0, 0, 0],       # 5 errors
    [69, 71, 145, 49, 70, 134, 0, 0, 0, 0, 0, 144, 228, 239, 62, 153, 67, 12]
]
msg_bytes_uncorrectable = [
    [0, 0, 0, 0, 0, 0, 173, 129, 195, 218, 3, 144, 228, 239, 62, 153, 67, 12],      # 6 errors
    [69, 71, 145, 49, 70, 134, 173, 129, 195, 218, 3, 144, 0, 0, 0, 0, 0, 0],       # 6 errors
]


class TestReedSolo(unittest.TestCase):

    def test_correctable_barcode(self):
        decoder = ReedSolomonDecoder()
        for case in msg_bytes_correctable:
            corrected = decoder.decode(case, num_ecc_bytes)
            self.assertEquals(msg_bytes, corrected)

    def test_uncorrectable_barcode(self):
        decoder = ReedSolomonDecoder()
        for case in msg_bytes_uncorrectable:
            self.assertRaises(ReedSolomonError, decoder.decode, case, num_ecc_bytes)


if __name__ == '__main__':
    unittest.main()