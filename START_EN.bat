@echo off
cd /d "%~dp0"
py -3 aria2_gui_downloader_ENG.py
if errorlevel 1 pause
