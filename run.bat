@echo off
rem NAJI - run from source without a console window
rem NOTE: keep this file pure ASCII + CRLF line endings.
cd /d "%~dp0"
if not exist "main.py" (
  echo   ERROR: run this file from the project folder (main.py not found).
  pause
  exit /b 1
)
start "Naji" /b pythonw main.py
