@echo off
REM Windows batch script for installing dependencies

echo 🚀 Installing live-video-editor dependencies for Windows...

pip install -r requirements-windows.txt

if %errorlevel% neq 0 (
    echo ❌ Installation failed!
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully!
echo.
echo To run the application:
echo python main.py
pause
