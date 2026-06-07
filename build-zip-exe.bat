@echo off
setlocal

set "APP_NAME=Notepad--"
set "VERSION=1.5"
set "PYTHON_EXE=C:\Users\Pearlong\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "ENTRY=phil_notepad_plus_1.5.py"
set "ICON=PhilNotepadPlus.ico"
set "DIST_DIR=dist\%APP_NAME%"
set "ZIP_DIR=release"
set "ZIP_FILE=%ZIP_DIR%\%APP_NAME%_v%VERSION%_win64.zip"

cd /d "%~dp0"

if not exist "%PYTHON_EXE%" (
    echo Python was not found:
    echo   %PYTHON_EXE%
    exit /b 1
)

if not exist "%ENTRY%" (
    echo Entry file was not found:
    echo   %ENTRY%
    exit /b 1
)

"%PYTHON_EXE%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller is not installed for this Python.
    echo Install it with:
    echo   "%PYTHON_EXE%" -m pip install pyinstaller
    exit /b 1
)

echo Cleaning previous build output...
if exist "build\%APP_NAME%" rmdir /s /q "build\%APP_NAME%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
if not exist "%ZIP_DIR%" mkdir "%ZIP_DIR%"
if exist "%ZIP_FILE%" del /q "%ZIP_FILE%"

echo Building folder-based executable...
"%PYTHON_EXE%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon "%ICON%" ^
    --add-data "welcome.txt;." ^
    "%ENTRY%"

if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Creating zip package...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%ZIP_FILE%' -Force"

if errorlevel 1 (
    echo Zip packaging failed.
    exit /b 1
)

echo Done.
echo Folder: %DIST_DIR%
echo Zip:    %ZIP_FILE%
endlocal
