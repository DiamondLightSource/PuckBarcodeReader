Using the Source Code - Windows
===============================
This application is written in Python (v3.6) and was developed under Windows but should be portable to other platforms.

The following steps will help you prepare an appropriate Python environment to run this program. These instructions assume that you will use the 64-bit version of Python 3.6.

* Install the appropriate version of Python by downloading the Windows binary installer from <https://www.python.org/downloads>
    * You want the one labelled 'Windows x86 MSI installer'
    * During installation, make sure you check ‘Add python.exe to system path’.
    
* The following packages are required:
    * pyperclip
    * numpy
    * scipy
    * opencv-python==3.1.0.5
    * PyQt5
    
* Download the source code for the Barcode scanner program from <https://github.com/DiamondLightSource/PuckBarcodeReader> 
* All of required packages can be installed using `pipenv`. To do this:
    * To create a new virtual environment with all dependencies installed run `pipenv install --dev`
*  Activate the virtual envirolment
*  `cd` into the dls_barcode folder. Then type `python main.py` to run the program.

Running Tests
========================
To run tests do: `pipenv run pytest`. This will run both the unittests and the system tests.

Creating a Self-Contained Executable
====================================
A Python package called [PyInstaller](http://www.pyinstaller.org/) can be used to create a stand-alone windows executable (.exe) file.

Activate your virtual environment (e.g.run in command line C:\Users\rqq82173\PycharmProjects\python_environments\barcode_qt5\Scripts\activate.bat) next run the `build.bat` in PuckBarcodeReader folder. This will create the file `bin\barcode.exe`. This will be fairly large (~40 MB). 
Once .exe file is created add 'resources' folder to th bin folder (resources include the icon and the shape patter). 
Zip the bin folder and add it to release files.

Continuous Integration
======================
The plan is to start using github actions.
