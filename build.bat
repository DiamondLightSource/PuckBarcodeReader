rd /S /Q bin
mkdir bin

cd dls_barcode

REM use to debug the exe file
REM pyinstaller --onefile --icon=..\resources\icons\qr_code.ico --debug --clean main.py

pyinstaller --onefile --windowed --icon=..\resources\icons\qr_code.ico --clean main.py

move dist\main.exe ..\bin\barcode.exe
rd /S /Q build
rd /S /Q dist
del main.spec

@echo start barcode.exe --config_file .\config.ini>"..\bin\launch_barcode.bat"
