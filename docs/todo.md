


* For single image scan i.e., from file, use the deep contour locator to locate finder patterns in the image. If multiple patterns are returned for the same location, read them all until you find a valid datamatrix. This will be especially helpful for the proposed tray scanning mode.


* Improve calculation of the unipuck geometry: find some way of filtering out obviously bad points.
* Add loading/progress dialog when scanning from file.


Datamatrix
----------
* Implement the rest of the data matrix interpretation specification, i.e., bytes 231-241
* Allow for different sizes of datamatrix symbol - automatically calculate the number of pixels based on the alternating edges of the finder pattern.
* Allow for different length messages - or automatically detect this
