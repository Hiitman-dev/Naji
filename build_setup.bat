@echo off
rem NAJI - step 2: build the installer Output\NajiSetup.exe with Inno Setup
rem NOTE: keep this file pure ASCII + CRLF line endings.
rem       (UTF-8 text or LF-only endings make cmd abort instantly,
rem        which closed the window before "pause" could run.)
cd /d "%~dp0"

echo ==================================================
echo   NAJI  -  BUILD INSTALLER   (step 2 of 2)
echo   This window STAYS OPEN. If anything fails,
echo   the error text stays visible - screenshot it.
echo ==================================================
echo.

echo [1/3] Checking dist\Naji.exe ...
if not exist "dist\Naji.exe" (
  echo.
  echo   ERROR: dist\Naji.exe not found.
  echo   First double-click  build_exe.bat  to build it,
  echo   then run this file again.
  echo.
  pause
  exit /b 1
)
echo       OK.
echo.

echo [2/3] Looking for Inno Setup 6 (ISCC.exe) ...
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo.
  echo   ERROR: Inno Setup 6 is not installed.
  echo   Download it FREE from:   https://jrsoftware.org/isdl.php
  echo   Install it with default options, then run this file again.
  echo.
  pause
  exit /b 1
)
echo       OK:  "%ISCC%"
echo.

echo [3/3] Compiling installer (about a minute) ...
"%ISCC%" setup.iss
if errorlevel 1 (
  echo.
  echo   ERROR: Inno Setup compile failed.
  echo   Read the error text above and screenshot it if unclear.
  echo.
  pause
  exit /b 1
)

echo.
echo       Making the release zip (installer only) ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'Output\NajiSetup.exe' -DestinationPath 'Naji-Setup.zip' -Force"
if errorlevel 1 (
  echo       (zip step failed - but the installer itself is ready)
) else (
  echo       OK:  Naji-Setup.zip
)

echo.
echo ==================================================
echo   DONE!  The installer is ready:
echo      Output\NajiSetup.exe    (single-file installer)
echo      Naji-Setup.zip          (zip of the same file)
echo.
echo   Distribute ONLY these files to users - never the
echo   project folder.  When a user runs NajiSetup.exe
echo   they get the full wizard: language - welcome -
echo   CHOOSE DRIVE/FOLDER - start menu - desktop icon -
echo   install - launch, just like classic installers.
echo ==================================================
pause
exit /b 0
