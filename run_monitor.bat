@echo off
:: ──────────────────────────────────────────────────────────
::  HDD Monitor Launcher
::  Runs hdd_monitor.py silently in the background
::  Place this file in the ROOT of your External HDD
:: ──────────────────────────────────────────────────────────

:: Change to the directory where this .bat file lives
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python from https://python.org
    pause
    exit /b 1
)

:: Run the monitor script silently (hidden window)
start "" /min pythonw hdd_monitor.py

:: If pythonw is not available, fall back to python
if %errorlevel% neq 0 (
    start "" /min python hdd_monitor.py
)

exit /b 0
