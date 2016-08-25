Data Matrix Reading
===================
A datamatrix is a way of encoding a string of data in a symbol. The principles of datamatrix encoding are described in the [datamatrix](docs/datamatrix.md) document.

Before a datamatrix can be read from an image, it must first be located. In this application, this is achieved using a few different algorithms described in the [locator algorithms](docs/datamatrix-locator.md) document. These location algorithms return a `FinderPattern` object (`datamatrix\finder_pattern.py`) which describes the location, orientation, and size of the datamatrix.

A `DataMatrix` object (`datamatrix\datamatrix.py`) is used to represent a datamatrix in the application. It takes a `FinderPattern` in its constructor and has a `perform_read()` method which recovers the data that the datamatrix encodes following the procedure outlined below. All of the code responsible for reading a datamatrix is found in `datamatrix\read\`.

Reading the Bit Pattern
-----------------------
The `FinderPattern` describes the location, in image pixels, of the corners of the datamatrix. Since we already know how many cells make up the datamatrix (14x14 by default for our barcodes), we can use this information to infer the center position of each cell of the datamatrix. 

For each cell, we then calculate its the brightness by looking at the pixels in a very small area surrounding the cell's center. If the pixels are mostly black then the cell is a '1' bit, and if they are mostly white then the cell is a '0' bit. This reading process is inherently fuzzy and it is quite possible for errors to be made; however this is mitigated by the later use of error correction.

The end result of this process is a square array of bits (0s and 1s). We ignore the cells that make up the border since they do not encode any data.

This routine is implemented in `datamatrix\read\read.py`
 
Recovering the Message
----------------------
As explained in the encoding section of the [datamatrix](docs/datamatrix.md) document, the datamatrix symbol is divided into a series of shapes (called 'Utahs'), each of which contains 8 pixels and thus encodes a single byte.

The next step is to run an algorithm (`datamatrix\read\decode.py`) that extracts these shapes from bit array, thereby converting the array into a series of bytes. Each of these bytes is just a number between 0 and 255.

This series of bytes is passed to the Reed-Solomon decoder (`datamatrix\read\reedsolo.py`), which corrects any errors, returning a list of corrected bytes.

Finally, the corrected bytes are interpreted according to the datamatrix specification, returning the original message (`datamatrix\read\interpret.py`).



