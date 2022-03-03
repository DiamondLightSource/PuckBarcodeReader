* Improve calculation of the unipuck geometry: find some way of filtering out obviously bad points.

Datamatrix
----------
* Implement the rest of the data matrix interpretation specification, i.e., bytes 231-241
* Allow for different sizes of datamatrix symbol - automatically calculate the number of pixels based on the alternating edges of the finder pattern.
