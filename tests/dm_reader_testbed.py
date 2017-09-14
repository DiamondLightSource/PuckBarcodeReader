from dls_barcode.datamatrix import DataMatrix
from dls_util import Image, Color

dm_img_file = './test-resources/test/dm6.png'

dm_img = Image.from_file(dm_img_file)
mono_img = dm_img.to_grayscale()


barcodes = DataMatrix.locate_all_barcodes_in_image(mono_img, matrix_sizes=18)

for barcode in barcodes:
    barcode.draw(dm_img, Color.Green())
    barcode.perform_read()
    print(barcode.data())
    print(barcode._error_message)

dm_img.popup()



from dls_barcode.datamatrix.read import ReedSolomonDecoder

# msg = 16, 16 ecc
chars = [69, 71, 145, 49, 70, 134, 173, 69, 71, 145, 49, 70, 134, 173, 129]

decoder = ReedSolomonDecoder()

out = decoder.encode(chars, 17)
print([int(b) for b in out], len(out))


