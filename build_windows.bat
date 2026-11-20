@echo off
rem Build ServoController.exe on Windows. Needs Python 3.10+ on PATH.
rem Run from the folder that contains the "app" folder.
python -m pip install --upgrade pip pyinstaller PySide6 || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name ServoController ^
  --collect-all PySide6 ^
  --add-data "app\Main.qml;." ^
  app\main.py || exit /b 1
echo.
echo Done: dist\ServoController.exe
