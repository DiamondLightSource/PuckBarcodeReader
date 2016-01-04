datamatix Package
-----------------
The datamatrix package is used to read all of the Data Matrix 2D barcodes in a supplied grayscale image. For more information on Data Matrix, see the Wikipedia article:

<https://en.wikipedia.org/wiki/Data_Matrix>

The package expects the Data Matricies to be of the 'ECC 200' type (the latest type at the time of writing). This type of Data Matrix makes use of Reed-Solomon codes for error correction which means that the entire symbol encoded in the message can still be read successfully even if some of the matrix is damaged or unreadable.

Currently, the code is set up to expect only 14x14 Data Matricies (with a 12x12 data area), with 8 bytes used for data and 10 for ECC (18 bytes total).

The complete specification for ECC 200 Data Matrix can be found here:

<http://barcode-coder.com/en/datamatrix-specification-104.html>

Some of the code in the package is based on the zxing barcode reading library:

<https://github.com/zxing/zxing>

The code use for Reed-Solomon decoding is a modified version of that obtained from:

<https://pypi.python.org/pypi/reedsolo>