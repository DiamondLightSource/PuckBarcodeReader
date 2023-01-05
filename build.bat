rd /S /Q bin
mkdir bin

REM use to debug the exe file
REM pyinstaller --onefile --icon=..\resources\icons\qr_code.ico --debug --clean main.py

pyinstaller --onefile --add-binary "C:\Users\rqq82173\.virtualenvs\PuckBarcodeReader-6rTXUiM6\Lib\site-packages\pylibdmtx\libdmtx-64.dll;." --windowed --icon="resources\icons\qr_code.ico" --clean "main.py"

move dist\main.exe bin\barcode.exe
rd /S /Q build
rd /S /Q dist
del main.spec
