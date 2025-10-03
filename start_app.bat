@echo off
echo ========================================
echo   Email Automation System Startup
echo ========================================
echo.

REM Check if Python 3.11 is available
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from https://python.org
    pause
    exit /b 1
)

echo Python 3.11 found. Setting up environment...
echo.

REM Create virtual environment if it doesn't exist
if not exist ".venv311" (
    echo Creating Python 3.11 virtual environment...
    py -3.11 -m venv .venv311
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call .\.venv311\Scripts\activate.bat

REM Check if requirements are installed
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo Dependencies installed successfully.
) else (
    echo Dependencies already installed.
)

echo.

REM Check if .env file exists, create template if not
if not exist ".env" (
    if exist "env.template" (
        echo Creating .env file from template...
        copy env.template .env
        echo.
        echo IMPORTANT: Please edit .env file with your configuration before starting the system!
        echo Opening .env file for editing...
        notepad .env
        echo.
        echo Press any key after you've configured your .env file...
        pause >nul
    ) else (
        echo ERROR: No .env file or env.template found!
        echo Please create a .env file with your configuration.
        pause
        exit /b 1
    )
)

echo Starting Email Automation System...
echo.
echo The web interface will open at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Start the server and open browser after a short delay
start "" "http://localhost:8000"
python server.py

echo.
echo Server stopped. Press any key to exit...
pause >nul





