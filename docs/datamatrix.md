Data Matrix
===========
A Data Matrix is a type of two-dimensional barcode similar to the popular QR code. The [wikipedia page](https://en.wikipedia.org/wiki/Data_Matrix) contains an excellent summary but we will cover the important details here.

Data Matrix symbols are rectangular and are composed of a grid of pixels which represent bits (black for 1, white for 0).

![Data Matrix](img/datamatrix.jpg)

Every Data Matrix is composed of two solid adjacent borders in an "L" shape (called the "finder pattern") and two other borders consisting of alternating dark and light "cells" or modules (called the "timing pattern"). Within these borders are rows and columns of cells encoding information. The finder pattern is used to locate and orient the symbol while the timing pattern provides a count of the number of rows and columns in the symbol.

While the symbols may vary in size from 10x10 to 144x144, **all of the barcodes we are currently using for the DLS barcode scanner are 14x14, with 12x12 data area.**
 
Encoding
--------
The Data Matrix symbol is divided into a series of shapes (often called 'Utahs'), each of which contains 8 pixels and thus encodes a single byte. The [Wikipedia article](https://en.wikipedia.org/wiki/Data_Matrix#Encoding) contains the following image which shows how the bytes for the string "Wikipedia" are encoded into the data matrix symbol:

![Data Matrix encoding](img/datamatrix-encoding.jpg)

The default encoding used is as follows:

| Byte Value | Interpretation             |
| ----------- | -------------------------- |
| 0           | Not used                    |
| 1 - 128     | ASCII data (ASCII value + 1) |
| 129         | End of message              |
| 130 – 229   | Digit pairs 00 – 99         |
| 230 - 241   | Other Datamatrix controls   |
| 242 - 255   | Not Used                    |






Error Correction Codes
----------------------



The `datamatrix` Package
------------------------
The datamatrix package is used to read all of the Data Matrix 2D barcodes in a supplied grayscale image. For more information on Data Matrix, see the Wikipedia article, <https://en.wikipedia.org/wiki/Data_Matrix>

The package expects the Data Matricies to be of the 'ECC 200' type (the latest type at the time of writing). This type of Data Matrix makes use of Reed-Solomon codes for error correction which means that the entire symbol encoded in the message can still be read successfully even if some of the matrix is damaged or unreadable.

Currently, the code is set up to expect only 14x14 Data Matricies (with a 12x12 data area), with 8 bytes used for data (including 1 for the EOM byte) and 10 for ECC (18 bytes total). Note that it is possible for the data matrix to encode more than 8 characters with 8 data bytes because some values in the data matrix specification encode digit pairs (00-99) in a single byte.

The complete specification for ECC 200 Data Matrix can be found here: <http://barcode-coder.com/en/datamatrix-specification-104.html>

Some of the code in the package is based on the zxing barcode reading library: <https://github.com/zxing/zxing>

The code use for Reed-Solomon decoding is a modified version of that obtained from: <https://pypi.python.org/pypi/reedsolo>