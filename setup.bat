@echo off
REM Setup Script for Social Support AI Application (Windows)
REM This script creates a virtual environment and installs dependencies

echo ========================================
echo Social Support AI - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Upgrading pip...
python -m pip install --upgrade pip

echo [4/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 1.1 On Unix or MacOS: source venv/bin/activate
echo 2. Copy .env.example to .env: copy .env.example .env
echo 3. Make sure Ollama is running with llama3.2 model
echo 3.1 ollama serve
echo 3.2 ollama pull llama3.2
echo 4. Run the demo: python demo.py
echo.

pause
