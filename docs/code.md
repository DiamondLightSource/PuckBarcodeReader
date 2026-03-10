Using the Source Code - Windows
===============================
This application is written in Python and was developed under Windows but should be portable to other platforms. It as been updated to python 3.14 in release 1.10.0.

The following steps will help you prepare an appropriate Python environment to run this program. These instructions assume that you will use the 64-bit version of Python 3.14.

* Install the appropriate version of Python by downloading the Windows binary installer from <https://www.python.org/downloads>
    * You want the one labelled 'Windows x86 MSI installer'
    * During installation, make sure you check ‘Add python.exe to system path’.
    
* The following packages are required:
    * pyperclip
    * numpy
    * scipy
    * opencv-python
    * PyQt5
    * pylibdmtx
    * pyinstaller
    
* Download the source code for the Barcode scanner program from <https://github.com/DiamondLightSource/PuckBarcodeReader> 
* All of required packages can be installed using `pipenv`. To do this:
    * To create a new virtual environment with all dependencies installed run `pipenv install --dev`. Alternatively you can use pip to install each of the needed dependency after creating and activating a new virtual envirolment.
*  Activate the virtual envirolment
* You may encounter a missing dll error - libdmtx-64.dll - which is required by pylibdmt. You can work around this problem by downloading the dll from: https://github.com/NaturalHistoryMuseum/pylibdmtx/issues/64  and manually adding it to you virtual env (.venv\Lib\site-packages\pylibdmtx\libdmtx-64.dll).
*  `cd` into the dls_barcode folder. Then type `python main.py` to run the program.

Running Tests
========================
To run tests do: `pipenv run pytest`. This will run both the unittests and the system tests.

Creating a Self-Contained Executable
====================================
A Python package called [PyInstaller](http://www.pyinstaller.org/) can be used to create a stand-alone windows executable (.exe) file.

Activate your virtual environment (e.g.run in command line C:\Users\rqq82173\PycharmProjects\python_environments\barcode_qt5\Scripts\activate.bat) next run the `build.bat` in PuckBarcodeReader folder. 
Note build.bat includes hardcoded path to libdmtx-64.dll - it has to be updated accordingly before running `bin\barcode.exe`.
This will create the file `bin\barcode.exe`. This will be fairly large (~40 MB). 
Once .exe file is created add 'resources' folder to th bin folder (resources include the icon and the shape patter). 
Zip the bin folder and add it to release files.

Continuous Integration
======================
The plan is to start using github actions.
