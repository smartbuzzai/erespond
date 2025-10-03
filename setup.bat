@echo off
echo ========================================
echo   Email Automation System Setup
echo ========================================
echo.

REM Check if Python 3.11 is available
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 not found!
    echo.
    echo Please install Python 3.11:
    echo 1. Go to https://python.org/downloads/
    echo 2. Download Python 3.11.x
    echo 3. Run the installer and make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo Python 3.11 found: 
py -3.11 --version
echo.

REM Create virtual environment
echo Creating Python 3.11 virtual environment...
py -3.11 -m venv .venv311
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)

echo Virtual environment created successfully.
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .\.venv311\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo Dependencies installed successfully.
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    if exist "env.template" (
        echo Creating .env file from template...
        copy env.template .env
        echo.
        echo IMPORTANT: Configuration required!
        echo.
        echo The .env file has been created with default values.
        echo You MUST edit this file with your actual configuration:
        echo.
        echo 1. OpenAI API key (get from https://platform.openai.com/api-keys)
        echo 2. Gmail credentials (email + app password)
        echo 3. Google Chat webhook URL
        echo.
        echo Opening .env file for editing...
        notepad .env
    ) else (
        echo ERROR: No env.template found!
        echo Please create a .env file manually.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the Email Automation System:
echo   1. Double-click start_app.bat
echo   2. Or run: start_app.bat
echo.
echo The web interface will be available at:
echo   http://localhost:8000
echo.
echo Press any key to exit...
pause >nul





