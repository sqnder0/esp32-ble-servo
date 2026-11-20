@echo off
rem Build ServoController.exe on Windows. Needs Python 3.10+ on PATH.
rem Run from the project folder (the one that contains the "app" folder).
rem The venv lives in C:\sv (short path) to avoid the Windows long-path limit
rem that breaks pip installs of PySide6 under the Microsoft Store Python.
setlocal
if not exist C:\sv\Scripts\python.exe (
  python -m venv C:\sv || exit /b 1
)
C:\sv\Scripts\python -m pip install --upgrade pip || exit /b 1
C:\sv\Scripts\python -m pip install pyinstaller PySide6_Essentials PySide6_Addons || exit /b 1
C:\sv\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name ServoController ^
  --collect-all PySide6 ^
  --add-data "app\Main.qml;." ^
  app\main.py || exit /b 1
echo.
echo Done: dist\ServoController.exe
