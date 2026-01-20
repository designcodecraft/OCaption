@echo off
REM build_exe.bat - Builds captioner.exe using the project's virtualenv and PyInstaller
REM Run this from the project root (D:\codebase\cap) in a regular Command Prompt (not PowerShell).

:: Activate venv
call "%~dp0\.venv\Scripts\activate.bat"
if errorlevel 1 (
  echo Failed to activate virtualenv. Ensure .venv exists and contains Scripts\activate.bat
  exit /b 1
)

:: Ensure PyInstaller is installed in venv
python -m pip install --upgrade pip
python -m pip install pyinstaller --upgrade

:: Read name/version/icon from app_meta.json via PowerShell
for /f "delims=" %%A in ('powershell -NoProfile -Command ^
  "(Get-Content -Raw 'app_meta.json' | ConvertFrom-Json).name"') do set APP_NAME=%%A
for /f "delims=" %%A in ('powershell -NoProfile -Command ^
  "(Get-Content -Raw 'app_meta.json' | ConvertFrom-Json).version"') do set APP_VER=%%A
for /f "delims=" %%A in ('powershell -NoProfile -Command ^
  "(Get-Content -Raw 'app_meta.json' | ConvertFrom-Json).icon"') do set APP_ICON=%%A

set EXE_NAME=%APP_NAME%_v%APP_VER%

:: Build single-file, GUI (no console) executable with minimal dependencies
:: Exclude bloat: torch, numpy, scipy, whisper, sounddevice, torchaudio, etc.
:: Using ^ for line continuation in batch
pyinstaller --noconsole --onefile --name "%EXE_NAME%" ^
  --icon "%APP_ICON%" ^
  --add-data "app_meta.json;." ^
  --add-data "assets\icon.ico;assets" ^
  --add-data "live_caption_reader.py;." ^
  --hidden-import=pywinauto ^
  --exclude-module=torch ^
  --exclude-module=numpy ^
  --exclude-module=scipy ^
  --exclude-module=sounddevice ^
  --exclude-module=openai ^
  --exclude-module=whisper ^
  --exclude-module=torchaudio ^
  --exclude-module=torchvision ^
  captioner.py

if exist dist\%EXE_NAME%.exe (
  echo Build succeeded: dist\%EXE_NAME%.exe
) else (
  echo Build finished but dist\%EXE_NAME%.exe not found. See PyInstaller output above for errors.
)

:: Deactivate venv (optional)
deactivate 2>nul || @rem
pause