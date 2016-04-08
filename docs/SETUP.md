Using the Source Code - Windows
===============================
This application is written in Python (v3.4) and was developed under Windows but should be portable to other platforms.

The following steps will help you prepare an appropriate Python environment to run this program. These instructions assume that you will use the 32-bit version on Python 3.4.4, but the barcode scanner should also run correctly under other versions of Python (e.g. 2.7, 3.5, 64bit).

* Install the appropriate version of Python by downloading the Windows binary installer from <https://www.python.org/downloads/release/python-344/>
    * You want the one labelled 'Windows x86 MSI installer'
    * During installation, make sure you check ‘Add python.exe to system path’.
    
* The following packages are required:
    * pyperclip
    * enum [only if using Python v2.7]
    * numpy
    * scipy
    * OpenCV
    * PyQt4
    
* Some of these packages can be installed using `pip`. To do this:
    * Open cmd.exe (being sure to ‘Run as Administrator’)
    * Upgrade pip by typing `pip install –-upgrade pip`
    * Install pyperclip by typing `pip install pyperclip`
    * Install enum by typing `pip install enum` [only if using Python 2.7]
    
* The easiest way to install the other packages is to download the precompiled binaries from <http://www.lfd.uci.edu/~gohlke/pythonlibs/>. To install each one, open cmd.exe and type `pip install filename`. Download the most recent version of each for your version of Python (3.4, 32bit), e.g.:
    * numpy-1.11.0+mkl-cp34-cp34m-win32.whl
    * opencv_python-3.1.0-cp34-none-win32.whl
    * scipy-0.17.0-cp34-none-win32.whl
    * PyQt4-4.11.4-cp34-none-win32.whl
    
* Download the source code for the Barcode scanner program from <https://github.com/krisward/dls_barcode> - use the ‘Download ZIP’ link. Open the zip and extract the contents to a suitable folder.

* Open cmd.exe and navigate to the above folder. `cd` into the dls_barcode folder. Then type `python main.py` to run the program.









