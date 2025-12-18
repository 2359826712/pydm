@echo off
echo ==========================================
echo Packging loader.exe (Including dependencies)...
echo ==========================================

REM Activate venv if exists
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

REM PyInstaller packaging command
REM -F: One file
REM --hidden-import: Force include libraries for main.py
pyinstaller -F loader.py ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import pythoncom ^
    --hidden-import ctypes ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import time ^
    --hidden-import requests ^
    --clean

echo.
echo ==========================================
echo Done!
echo Check dist/loader.exe
echo ==========================================
pause
