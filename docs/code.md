Using the Source Code - Windows
===============================
This application is written in Python (v3.5) and was developed under Windows but should be portable to other platforms.

The following steps will help you prepare an appropriate Python environment to run this program. These instructions assume that you will use the 32-bit version of Python 3.5.1, but the barcode scanner should also run correctly under other versions of Python (e.g. 2.7, 3.4, 64bit).

* Install the appropriate version of Python by downloading the Windows binary installer from <https://www.python.org/downloads/release/python-351/>
    * You want the one labelled 'Windows x86 MSI installer'
    * During installation, make sure you check ‘Add python.exe to system path’.
    
* The following packages are required:
    * pyperclip
    * enum [only if using Python v2.7]
    * numpy
    * scipy
    * opencv-python==3.1.0.5
    * PyQt5
    
* All of these packages can be installed using `pip`. To do this:
    * Create a new virtual environment eg.`python3 -m venv my-env`
    * activate the environment - run `my-env\Scripts\activate.bat`
    * Upgrade pip by typing `pip install –-upgrade pip`
    * Install all required packages using pip:
    * Install pyperclip by typing `pip install pyperclip`
    * Install enum by typing `pip install enum` [only if using Python 2.7]
    * Similarly install scipy, numpy, PyQt5 and opencv-python

NOTE: there is a requirements.txt file that was created for use by the CI server Travis. It contains all of the above dependencies except for enum.
    
* Download the source code for the Barcode scanner program from <https://github.com/DiamondLightSource/PuckBarcodeReader> - use the ‘Download ZIP’ link. Open the zip and extract the contents to a suitable folder.

* Open cmd.exe and navigate to the above folder. `cd` into the dls_barcode folder. Then type `python main.py` to run the program.

* To run the tests, you will need to install the nose and mock packages:
   * `pip install nose`
   * `pip install mock`

Running the System Tests
========================
For the paths in the system tests to work with nosetests, the working directory must be the top project folder (i.e. that's how the Travis CI server runs them - see below).

Unfortunately I can't get Pycharm to give me a Nosetests option when I right-click on the top Project directory in the Project tree. The way around this is to manually edit the working directory in the Pycharm Run configuration for "Nosetests in tests" (Run -> Edit Configurations, then look at the entries in the "Python tests" tree) to be the top Project directory, so when we right-click on the tests/ directory and select "Nosetests in tests" it's pointing at the right path! 

Alternatively, we can simply run "nosetests" from the command line, in the top Project directory.

Creating a Self-Contained Executable
====================================
A Python package called [PyInstaller](http://www.pyinstaller.org/) can be used to create a stand-alone windows executable (.exe) file.

Activate your virtual environment (e.g.run in command line C:\Users\rqq82173\PycharmProjects\python_environments\barcode_qt5\Scripts\activate.bat) 
Install PyInstaller with `pip install pyinstaller` (if it is not installed yet).

To create the executable file, run the `build.bat` file. This will create the file `bin\barcode.exe`. This will be fairly large (~40 MB). 
'build.bat' includes hardcoded paths to the main file and the icon. This needs to be updated accordingly.
Once .exe file is created add 'resources' folder to th bin folder (resources include the icon and the shape patter). 
Zip the bin folder and add it to release files.

Continuous Integration
======================
[Travis CI](https://travis-ci.org/) was setup as the Continuous Integration server for this repository. You should be able to login with your GitHub credentials and see the repository there. The configuration file for Travis is .travis.yml in the root directory.

