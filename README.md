DLS Barcode Scanner Readme
==========================

Background and Description of Problem
-------------------------------------
i04-1 is high throughput beamline at Diamond Light Source (see the [i04-1 site](http://www.diamond.ac.uk/Beamlines/Mx/I04-1.html) for more). Crystal samples to be imaged on the beamline are first loaded onto sample pins of the the kind pictured below:

![Sample Pin](docs/img/pin.jpg) 

Each sample pin has a datamatrix barcode printed on the top for identification and tracking:

![Barcode on top of pin](docs/img/pin-barcode.jpg)

Each sample pin is loaded into a numbered position in a storage puck which is then stored under liquid nitrogen until they are ready to be imaged on the beamline. When the are imaged, a robot arm removes the pin from the puck, scans the barcode, and places the sample in the beam. The x-ray image is then associated with the barcode number. The current 16-pin puck design as pictured below is produced by Crystal Positioning systems (see [The CPS website](http://www.crystalpositioningsystems.com/index.php?option=com_content&view=article&id=21)). In the future a new type of 81-pin holder being developed in-house may also be used.

![Puck](docs/img/puck.jpg)

Once the samples have been loaded onto a pin and placed into a puck, the barcodes of each of the pins must be scanned in order to track the sample. Currently this is done with a small specialized barcode scanner that scans one barcode at a time. This takes several seconds per pin and is quite tedious. Also the reader is relatively expensive and difficult to configure.

The proposed solution to this problem is to create an application that can take an image of a puck from a standard camera, such as a webcam, and read the barcode from every pin, as well as determine each pin's numbered position. This would much quicker than individual scans and so would save a lot of time and frustration for beamline staff and users. Further such a solution would be very cheap to deploy as it would only require a copy of the application and a cheap off-the-shelf webcam. This means that it could be easily distributed to other institutions with similar requirements and external users who need to prepare sample pucks for imaging.

This repository contains an implementation of this solution. This document is intended to provide enough information to enable other developers to modify this application by introducing new functionality or fixing existing problems.


Using the Source Code
---------------------
This application is written in Python (v3) and was developed under Windows but should be portable to other platforms.
 
Please see the [Setup Instructions](docs/SETUP.md) for details of how to prepare your environment to run this source code.



The `datamatrix` Package
------------------------
The datamatrix package is used to read all of the Data Matrix 2D barcodes in a supplied grayscale image. For more information on Data Matrix, see the Wikipedia article, <https://en.wikipedia.org/wiki/Data_Matrix>

The package expects the Data Matricies to be of the 'ECC 200' type (the latest type at the time of writing). This type of Data Matrix makes use of Reed-Solomon codes for error correction which means that the entire symbol encoded in the message can still be read successfully even if some of the matrix is damaged or unreadable.

Currently, the code is set up to expect only 14x14 Data Matricies (with a 12x12 data area), with 8 bytes used for data (including 1 for the EOM byte) and 10 for ECC (18 bytes total). Note that it is possible for the data matrix to encode more than 8 characters with 8 data bytes because some values in the data matrix specification encode digit pairs (00-99) in a single byte.

The complete specification for ECC 200 Data Matrix can be found here: <http://barcode-coder.com/en/datamatrix-specification-104.html>

Some of the code in the package is based on the zxing barcode reading library: <https://github.com/zxing/zxing>

The code use for Reed-Solomon decoding is a modified version of that obtained from: <https://pypi.python.org/pypi/reedsolo>


The `plate` Package
-------------------
