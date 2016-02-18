Using the Source Code - Windows
===============================
This application is written in Python (v3.4) and was developed under Windows but should be portable to other platforms.

The following steps will help you prepare an appropriate python environment to run this program. Run the file 'gui.py' to launch the prgoram.

* Install the appropriate version of Python by downloading the windows binary installer from:
    <https://www.python.org/downloads/release/python-344/>

* Install PyQt4:
    * Windows binary from: <https://riverbankcomputing.com/software/pyqt/download>
    * Get the latest version of PyQt4 for your version of Python (Python 3.4, 32 or 64bit)

* Install numpy:
    * Windows binary from: <http://sourceforge.net/projects/numpy/files/NumPy/>
    * Note that at time of writing 1.10.2 had windows binaries but 1.10.4 didn't

* Install scipy:
    * Windows binary from: <http://sourceforge.net/projects/scipy/files/scipy/>

* Install 'wheel' (`pip install wheel`)
    * wheel is the new standard for python package distribution; needed to install opencv
    * Note when installing using pip, you may have to run your command line as administrator

* Install opencv
    * Note: OpenCV themselves do not seem to provide an installer that is compatible with Python 3.4
    * Download the appropriate wheel file from: <http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv> (probably opencv_python-3.1.0-cp34-none-win32.whl or opencv_python-3.1.0-cp34-none-win_amd64.whl depending on whether you have 32-bit or 64-bit Python).
    * Install the wheel file with `pip install file_name`

* Install pyperclip (`pip install pyperclip`)




