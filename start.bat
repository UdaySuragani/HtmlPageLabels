@echo off
echo ========================================
echo  HTML Page Labels - Flask Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python found!
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [SUCCESS] Virtual environment created!
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet
echo [SUCCESS] Dependencies installed!
echo.

REM Run the Flask application
echo [INFO] Starting Flask application...
echo [INFO] Application will be available at: http://127.0.0.1:5000
echo [INFO] Press CTRL+C to stop the server
echo.
python app.py

REM Deactivate on exit
deactivate
