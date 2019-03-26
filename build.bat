rd /S /Q bin
mkdir bin

cd dls_barcode

REM use to debug the exe file
REM pyinstaller --onefile --icon=..\resources\icons\qr_code.ico --debug --clean main.py

pyinstaller --onefile --windowed --icon="C:\Users\rqq82173\PycharmProjects\PuckBarcodeReader\resources\icons\qr_code.ico" --add-data "C:\Users\rqq82173\PycharmProjects\PuckBarcodeReader\resources; C:\Users\rqq82173\PycharmProjects\PuckBarcodeReader\bin" --clean "C:\Users\rqq82173\PycharmProjects\PuckBarcodeReader\dls_barcode\main.py"

move dist\main.exe ..\bin\barcode.exe
rd /S /Q build
rd /S /Q dist
del main.spec
