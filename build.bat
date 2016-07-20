rd /S /Q bin
mkdir bin

cd dls_barcode

pyinstaller --onefile --windowed main.py

move dist\main.exe ..\bin\barcode.exe
rd /S /Q build
rd /S /Q dist
del main.spec