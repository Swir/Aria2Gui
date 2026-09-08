@echo off
cd /d "%~dp0"
py -3 aria2_gui_downloader_PL.py
if errorlevel 1 pause
