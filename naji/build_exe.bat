@echo off
rem NAJI - step 1: build dist\Naji.exe with PyInstaller
rem NOTE: keep this file pure ASCII + CRLF line endings.
rem       (UTF-8 text or LF-only endings make cmd abort instantly,
rem        which closed the window before "pause" could run.)
cd /d "%~dp0"

echo ==================================================
echo   NAJI  -  BUILD EXE   (step 1 of 2)
echo   This window STAYS OPEN. If anything fails,
echo   the error text stays visible - screenshot it.
echo ==================================================
echo.

rem ---- find Python (python.exe or py launcher) ----
set "PY="
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY goto nopython

echo [1/6] Python found:
%PY% --version
echo.

echo [2/6] Installing required packages (needs internet)...
echo       pyinstaller PySide6 requests jdatetime
%PY% -m pip install pyinstaller PySide6 requests jdatetime
if errorlevel 1 (
  echo.
  echo   ERROR: pip install failed. Check your internet connection
  echo   and run this file again.
  echo.
  pause
  exit /b 1
)
echo.

echo [3/6] Building dist\Naji.exe with PyInstaller (a few minutes)...
setlocal enabledelayedexpansion
set "FONT_ARGS="
for %%F in (assets\fonts\*.ttf) do set "FONT_ARGS=!FONT_ARGS! --add-data "%%F;assets\fonts""
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name Naji ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebChannel ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtPdf ^
  --exclude-module PySide6.QtSql ^
  --exclude-module PySide6.QtTest ^
  --hidden-import PySide6.QtSvg ^
  --add-data "assets\icon.ico;assets" ^
  %FONT_ARGS% ^
  --icon "assets\icon.ico" ^
  main.py
if errorlevel 1 (
  echo.
  echo   ERROR: PyInstaller build failed.
  echo   Read the error text above (most often: a red "No module named ..."
  echo   or a missing file). Fix it, then run this file again.
  echo.
  pause
  exit /b 1
)
endlocal
echo.

echo [4/6] Checking output...
if not exist "dist\Naji.exe" (
  echo   ERROR: dist\Naji.exe not found.
  echo   Scroll up - PyInstaller printed the problem somewhere above.
  echo.
  pause
  exit /b 1
)

rem ---- [5/6] Authenticode code signing (v6.0 - optional but recommended) ----
rem If certs\code_signing.pfx exists, dist\Naji.exe is signed automatically.
rem Without it the build still works - but Windows SmartScreen will warn
rem users. See docs\CODE_SIGNING.md for how to get a certificate.
rem Password can come from environment variable NAJI_CERT_PASS (safer than
rem hardcoding it in this file).
set "CERTFILE=certs\code_signing.pfx"
set "SIGNTOOL="
if exist "%CERTFILE%" (
  echo [5/6] Signing dist\Naji.exe with Authenticode certificate...
  for %%V in (6.0 6.1 6.2 6.3 10.0) do (
    if not defined SIGNTOOL (
      if exist "%ProgramFiles(x86)%\Windows Kits\10\bin\%%V\x64\signtool.exe" set "SIGNTOOL=%ProgramFiles(x86)%\Windows Kits\10\bin\%%V\x64\signtool.exe"
    )
  )
  if not defined SIGNTOOL (
    for /f "delims=" %%F in ('where signtool 2^>nul') do if not defined SIGNTOOL set "SIGNTOOL=%%F"
  )
  if not defined SIGNTOOL (
    echo   WARNING: cert found but signtool.exe not found.
    echo   Install "Windows SDK Signing Tools" or add signtool to PATH.
    echo   The EXE stays UNSIGNED this time.
  ) else (
    if not defined NAJI_CERT_PASS (
      echo   WARNING: set environment variable NAJI_CERT_PASS with the
      echo   certificate password, then run this file again. Skipped signing.
    ) else (
      "%SIGNTOOL%" sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /f "%CERTFILE%" /p "%NAJI_CERT_PASS%" "dist\Naji.exe"
      if errorlevel 1 (
        echo   ERROR: signing failed. Check the password and the PFX file.
        pause
        exit /b 1
      )
      "%SIGNTOOL%" verify /pa /v "dist\Naji.exe" | find /i "Issued to" 
      echo   OK: dist\Naji.exe is signed and timestamped.
    )
  )
) else (
  echo [5/6] Code signing skipped ^(certs\code_signing.pfx not found^).
  echo        Users may see a SmartScreen warning. Read docs\CODE_SIGNING.md
  echo        to fix this in 10 minutes.
)

echo.
echo ==================================================
echo   DONE!   Naji.exe is ready:   dist\Naji.exe
echo.
echo   NEXT STEP:  double-click  build_setup.bat
echo   (it turns Naji.exe into the signed installer NajiSetup.exe)
echo ==================================================
pause
exit /b 0

:nopython
echo.
echo   ERROR: PYTHON NOT FOUND  -  this is the most common reason
echo   why the old window opened and closed in a split second.
echo.
echo   Fix:
echo     1. Install Python from:  https://www.python.org/downloads/
echo     2. IMPORTANT: on the FIRST page of the Python installer,
echo        tick the checkbox:   [x] Add python.exe to PATH
echo        (without it Windows cannot find Python at all)
echo     3. Close this window and run build_exe.bat again.
echo.
pause
exit /b 1
