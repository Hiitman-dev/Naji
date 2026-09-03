@echo off
rem NAJI - environment doctor: shows what is installed and what is missing.
rem Run this FIRST if any build window closes or fails - screenshot its output.
rem NOTE: keep this file pure ASCII + CRLF line endings.
cd /d "%~dp0"

echo ==================================================
echo   NAJI  -  ENVIRONMENT CHECK
echo   This window STAYS OPEN.
echo ==================================================
echo.

echo [1/4] Python:
set "PY="
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if defined PY (
    echo       found:
    %PY% --version
) else (
    echo       NOT FOUND  -  install from https://www.python.org/downloads/
    echo                    and tick  [x] Add python.exe to PATH
)
echo.

echo [2/4] pip:
%PY% -m pip --version 2>nul
if errorlevel 1 echo       NOT FOUND  -  reinstall Python with "Add python.exe to PATH"
echo.

echo [3/4] PyInstaller:
%PY% -m PyInstaller --version 2>nul
if errorlevel 1 echo       not installed yet  (build_exe.bat installs it automatically)
echo.

echo [4/4] Inno Setup 6:
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    echo       found:  "%ISCC%"
) else (
    echo       NOT FOUND  -  install free from https://jrsoftware.org/isdl.php
)
echo.

echo ==================================================
echo   If all 4 steps are found/OK:
echo      1. double-click  build_exe.bat
echo      2. then double-click  build_setup.bat
echo.
echo   If something shows NOT FOUND, fix that step first.
echo   If an error appears - screenshot THIS window and
echo   send it, the window will not close by itself.
echo ==================================================
pause
exit /b 0
